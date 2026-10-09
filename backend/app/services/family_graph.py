"""Shared authorization and invariants for every family graph reader/writer."""
from collections import defaultdict, deque
from fastapi import HTTPException
from sqlalchemy import or_, text
from app.auth import has_site_wide_memorial_owner, is_global_admin
from app.models import (Memorial, MemorialAccess, FamilyRelationship, FamilyLinkPrivacy,
                        RelationshipType, UserRole)

REVERSE = {
    "parent": "child", "child": "parent", "adoptive_parent": "adoptive_child",
    "adoptive_child": "adoptive_parent", "step_parent": "step_child", "step_child": "step_parent",
    "spouse": "spouse", "ex_spouse": "ex_spouse", "partner": "partner",
    "sibling": "sibling", "half_sibling": "half_sibling",
}
PARENTS = {"parent", "adoptive_parent", "step_parent"}
CHILDREN = {"child", "adoptive_child", "step_child"}
SAME = {"spouse", "ex_spouse", "partner", "sibling", "half_sibling"}


def actual_owner(memorial, user):
    return bool(user and (memorial.owner_id == user.id or is_global_admin(user)))


def accessible_memorials(db, user):
    q = db.query(Memorial)
    if user and has_site_wide_memorial_owner(user):
        return q
    allowed = db.query(MemorialAccess.memorial_id).filter(MemorialAccess.user_id == user.id) if user else None
    return q.filter(or_(Memorial.is_public.is_(True), Memorial.id.in_(allowed))) if user else q.filter(Memorial.is_public.is_(True))


def visible_relationships(db, user, root_id=None):
    """Filter BEFORE traversal. Never bridge through an inaccessible page or edge."""
    pages = {m.id: m for m in accessible_memorials(db, user).all()}
    acl_ids = set()
    if user:
        acl_ids = {r[0] for r in db.query(MemorialAccess.memorial_id).filter(MemorialAccess.user_id == user.id).all()}
        acl_ids.update(mid for mid, m in pages.items() if m.owner_id == user.id)
    elevated = bool(user and has_site_wide_memorial_owner(user))
    policies = {(p.memorial_low, p.memorial_high): p.is_public for p in db.query(FamilyLinkPrivacy).all()}
    # Historical relations have no explicit consent: only the fictional demo
    # genealogy is publicly grandfathered. Other legacy relations stay visible to ACL holders.
    from en_memorials_manifest import EXPECTED_EN_NAMES
    rels = []
    for rel in db.query(FamilyRelationship).all():
        a, b = rel.memorial_id, rel.related_memorial_id
        if a not in pages or b not in pages:
            continue
        key = tuple(sorted((a, b)))
        public = policies.get(key, pages[a].language == "en" and pages[b].language == "en"
                              and pages[a].name in EXPECTED_EN_NAMES and pages[b].name in EXPECTED_EN_NAMES)
        if elevated or a in acl_ids or b in acl_ids or public:
            rels.append(rel)
    if root_id is None:
        return rels
    adj = defaultdict(set)
    for r in rels:
        adj[r.memorial_id].add(r.related_memorial_id)
        adj[r.related_memorial_id].add(r.memorial_id)
    connected = {root_id}
    queue = deque([root_id])
    while queue:
        for nb in adj[queue.popleft()]:
            if nb not in connected:
                connected.add(nb)
                queue.append(nb)
    return [r for r in rels if r.memorial_id in connected and r.related_memorial_id in connected]


def validate_link(db, a, b, rel_type, custom_label=None):
    # Serialize topology mutations so two individually valid concurrent writes
    # cannot jointly introduce a cycle. PostgreSQL lock lasts until commit/rollback.
    if db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(74291009)"))
    elif db.bind.dialect.name == "sqlite":
        connection = db.connection()
        if not connection.connection.driver_connection.in_transaction:
            connection.exec_driver_sql("BEGIN IMMEDIATE")
    t = rel_type.value if hasattr(rel_type, "value") else rel_type
    if a == b:
        raise HTTPException(400, "Cannot create relationship with itself")
    if t == "custom" and not (custom_label or "").strip():
        raise HTTPException(400, "custom_label is required for relationship_type=custom")
    all_rels = db.query(FamilyRelationship).all()
    for r in all_rels:
        rt = r.relationship_type.value
        oriented = rt if (r.memorial_id, r.related_memorial_id) == (a, b) else REVERSE.get(rt) if (r.memorial_id, r.related_memorial_id) == (b, a) else None
        if oriented == t:
            raise HTTPException(400, "Relationship already exists")
        if oriented and ((t in PARENTS and oriented in CHILDREN) or (t in CHILDREN and oriented in PARENTS)
                         or (t in SAME and oriented in PARENTS | CHILDREN)
                         or (t in PARENTS | CHILDREN and oriented in SAME)
                         or (t in {"spouse", "ex_spouse", "partner"} and oriented in {"spouse", "ex_spouse", "partner"})
                         or (t in {"sibling", "half_sibling"} and oriented in {"sibling", "half_sibling"})):
            raise HTTPException(409, "These relationships conflict. Remove the incorrect relationship first.")
    # Ancestor cycle: treat biological, adoptive and step parents consistently.
    parents = defaultdict(set)
    weighted = defaultdict(list)
    for r in all_rels:
        rt = r.relationship_type.value
        x, y = r.memorial_id, r.related_memorial_id
        if rt in PARENTS:
            parents[x].add(y)
            delta = -1
        elif rt in CHILDREN:
            parents[y].add(x)
            delta = 1
        elif rt in SAME:
            delta = 0
        else:
            continue
        weighted[x].append((y, delta))
        weighted[y].append((x, -delta))
    if t in PARENTS | CHILDREN:
        child, parent = (a, b) if t in PARENTS else (b, a)
        q, seen = [parent], set()
        while q:
            cur = q.pop()
            if cur == child:
                raise HTTPException(409, "This relationship would create an ancestor cycle")
            if cur not in seen:
                seen.add(cur)
                q.extend(parents[cur])
    if t in PARENTS | CHILDREN | SAME:
        expected = -1 if t in PARENTS else 1 if t in CHILDREN else 0
        generations = {a: 0}
        q = deque([a])
        while q:
            cur = q.popleft()
            for nb, d in weighted[cur]:
                if nb not in generations:
                    generations[nb] = generations[cur] + d
                    q.append(nb)
        if b in generations and generations[b] != expected:
            raise HTTPException(409, "This relationship conflicts with existing generations")


def store_link(db, a, b, data):
    """Caller validates and commits; both directions and visibility are atomic."""
    t = data.relationship_type.value if hasattr(data.relationship_type, "value") else data.relationship_type
    fields = dict(custom_label=data.custom_label, notes=data.notes)
    rel = FamilyRelationship(memorial_id=a, related_memorial_id=b,
                             relationship_type=RelationshipType(t),
                             nickname_for_visitor=data.nickname_for_visitor, **fields)
    db.add(rel)
    if t in REVERSE:
        db.add(FamilyRelationship(memorial_id=b, related_memorial_id=a,
                                 relationship_type=RelationshipType(REVERSE[t]), **fields))
    low, high = sorted((a, b))
    policy = db.query(FamilyLinkPrivacy).filter_by(memorial_low=low, memorial_high=high).first()
    if policy is None:
        db.add(FamilyLinkPrivacy(memorial_low=low, memorial_high=high, is_public=data.is_public))
    elif not data.is_public:
        policy.is_public = False  # Never silently broaden another existing relation.
    db.flush()
    return rel
