"""
API endpoints для работы с семейными связями и родословной.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Set, Optional
from collections import defaultdict
from sqlalchemy import and_, or_

from app.auth import get_current_user, get_optional_user, require_memorial_access
from app.db import get_db
from app.models import Memorial, FamilyRelationship, RelationshipType, User, UserRole
from app.schemas import (
    FamilyRelationshipCreate,
    FamilyRelationshipResponse,
    FamilyTreeResponse,
    FamilyTreeNode,
    ConnectionStep,
    HiddenConnection,
    HiddenConnectionsResponse,
    FullFamilyTreeResponse,
    FullTreeNode,
    FullTreeEdge,
    NetworkClustersResponse,
    NetworkCluster,
    NetworkClusterMember,
    NetworkBridge,
)

router = APIRouter(prefix="/family", tags=["family"])


@router.post("/memorials/{memorial_id}/relationships", response_model=FamilyRelationshipResponse, status_code=status.HTTP_201_CREATED)
async def create_relationship(
    memorial_id: int,
    relationship: FamilyRelationshipCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Создать семейную связь между мемориалами.

    Например:
    - memorial_id=1, related_memorial_id=2, relationship_type="parent"
      означает: мемориал 2 является родителем мемориала 1
    """
    require_memorial_access(memorial_id, current_user, db, min_role=UserRole.EDITOR)

    # Проверка существования мемориалов
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
    if not memorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memorial not found"
        )
    
    related_memorial = db.query(Memorial).filter(Memorial.id == relationship.related_memorial_id).first()
    if not related_memorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Related memorial not found"
        )
    
    # Проверка на самосвязь
    if memorial_id == relationship.related_memorial_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create relationship with itself"
        )
    
    # Проверка на дубликат
    existing = db.query(FamilyRelationship).filter(
        FamilyRelationship.memorial_id == memorial_id,
        FamilyRelationship.related_memorial_id == relationship.related_memorial_id,
        FamilyRelationship.relationship_type == relationship.relationship_type
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Relationship already exists"
        )
    
    # Валидация: для CUSTOM типа обязателен custom_label
    if relationship.relationship_type == RelationshipType.CUSTOM and not relationship.custom_label:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="custom_label is required for relationship_type=custom"
        )

    # Создание связи
    db_relationship = FamilyRelationship(
        memorial_id=memorial_id,
        related_memorial_id=relationship.related_memorial_id,
        relationship_type=relationship.relationship_type,
        custom_label=relationship.custom_label,
        notes=relationship.notes
    )
    db.add(db_relationship)

    # Таблица обратных связей: (тип → обратный тип, симметричная?)
    REVERSE_MAP = {
        RelationshipType.PARENT:          RelationshipType.CHILD,
        RelationshipType.CHILD:           RelationshipType.PARENT,
        RelationshipType.STEP_PARENT:     RelationshipType.STEP_CHILD,
        RelationshipType.STEP_CHILD:      RelationshipType.STEP_PARENT,
        RelationshipType.ADOPTIVE_PARENT: RelationshipType.ADOPTIVE_CHILD,
        RelationshipType.ADOPTIVE_CHILD:  RelationshipType.ADOPTIVE_PARENT,
        # Симметричные (обратный = тот же тип)
        RelationshipType.SPOUSE:          RelationshipType.SPOUSE,
        RelationshipType.EX_SPOUSE:       RelationshipType.EX_SPOUSE,
        RelationshipType.PARTNER:         RelationshipType.PARTNER,
        RelationshipType.SIBLING:         RelationshipType.SIBLING,
        RelationshipType.HALF_SIBLING:    RelationshipType.HALF_SIBLING,
        # CUSTOM — обратная не создаётся автоматически
    }

    reverse_type = REVERSE_MAP.get(relationship.relationship_type)
    if reverse_type is not None:
        # Проверяем, что обратная связь ещё не существует
        reverse_exists = db.query(FamilyRelationship).filter(
            FamilyRelationship.memorial_id == relationship.related_memorial_id,
            FamilyRelationship.related_memorial_id == memorial_id,
            FamilyRelationship.relationship_type == reverse_type
        ).first()
        if not reverse_exists:
            db.add(FamilyRelationship(
                memorial_id=relationship.related_memorial_id,
                related_memorial_id=memorial_id,
                relationship_type=reverse_type,
                custom_label=relationship.custom_label,
                notes=relationship.notes
            ))

    db.commit()
    db.refresh(db_relationship)

    return FamilyRelationshipResponse(
        id=db_relationship.id,
        memorial_id=db_relationship.memorial_id,
        related_memorial_id=db_relationship.related_memorial_id,
        relationship_type=db_relationship.relationship_type,
        custom_label=db_relationship.custom_label,
        notes=db_relationship.notes,
        related_memorial_name=related_memorial.name,
        created_at=db_relationship.created_at
    )


@router.get("/memorials/{memorial_id}/relationships", response_model=List[FamilyRelationshipResponse])
async def get_relationships(
    memorial_id: int,
    relationship_type: Optional[RelationshipType] = None,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Получить все семейные связи мемориала.

    Query параметры:
    - relationship_type: фильтр по типу связи (parent, child, spouse, sibling)
    """
    memorial = require_memorial_access(memorial_id, current_user, db, min_role=UserRole.VIEWER, allow_public=True)
    if not memorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memorial not found"
        )
    
    query = db.query(FamilyRelationship).filter(
        FamilyRelationship.memorial_id == memorial_id
    )
    
    if relationship_type:
        query = query.filter(FamilyRelationship.relationship_type == relationship_type)
    
    relationships = query.all()

    # Bulk-load связанных мемориалов — один запрос вместо N
    related_ids = {rel.related_memorial_id for rel in relationships}
    memorials_by_id = {}
    if related_ids:
        memorials_by_id = {
            m.id: m
            for m in db.query(Memorial).filter(Memorial.id.in_(related_ids)).all()
        }

    return [
        FamilyRelationshipResponse(
            id=rel.id,
            memorial_id=rel.memorial_id,
            related_memorial_id=rel.related_memorial_id,
            relationship_type=rel.relationship_type,
            custom_label=rel.custom_label,
            notes=rel.notes,
            related_memorial_name=memorials_by_id.get(rel.related_memorial_id, Memorial()).name,
            created_at=rel.created_at,
        )
        for rel in relationships
    ]


@router.delete("/relationships/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relationship(
    relationship_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Удалить семейную связь.
    Автоматически удаляет обратную связь, если она была создана автоматически.
    """
    relationship = db.query(FamilyRelationship).filter(FamilyRelationship.id == relationship_id).first()
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found"
        )

    # Проверяем EDITOR доступ к мемориалу связи
    require_memorial_access(relationship.memorial_id, current_user, db, min_role=UserRole.EDITOR)
    
    # Удаление обратной связи
    DELETE_REVERSE_MAP = {
        RelationshipType.PARENT:          RelationshipType.CHILD,
        RelationshipType.CHILD:           RelationshipType.PARENT,
        RelationshipType.STEP_PARENT:     RelationshipType.STEP_CHILD,
        RelationshipType.STEP_CHILD:      RelationshipType.STEP_PARENT,
        RelationshipType.ADOPTIVE_PARENT: RelationshipType.ADOPTIVE_CHILD,
        RelationshipType.ADOPTIVE_CHILD:  RelationshipType.ADOPTIVE_PARENT,
        RelationshipType.SPOUSE:          RelationshipType.SPOUSE,
        RelationshipType.EX_SPOUSE:       RelationshipType.EX_SPOUSE,
        RelationshipType.PARTNER:         RelationshipType.PARTNER,
        RelationshipType.SIBLING:         RelationshipType.SIBLING,
        RelationshipType.HALF_SIBLING:    RelationshipType.HALF_SIBLING,
    }
    reverse_type = DELETE_REVERSE_MAP.get(relationship.relationship_type)
    
    if reverse_type:
        reverse = db.query(FamilyRelationship).filter(
            FamilyRelationship.memorial_id == relationship.related_memorial_id,
            FamilyRelationship.related_memorial_id == relationship.memorial_id,
            FamilyRelationship.relationship_type == reverse_type
        ).first()
        if reverse:
            db.delete(reverse)
    
    db.delete(relationship)
    db.commit()
    
    return None


@router.get("/memorials/{memorial_id}/tree", response_model=FamilyTreeResponse)
async def get_family_tree(
    memorial_id: int,
    max_depth: int = 3,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Получить семейное дерево мемориала.

    Query параметры:
    - max_depth: максимальная глубина дерева (по умолчанию 3)
    """
    memorial = require_memorial_access(memorial_id, current_user, db, min_role=UserRole.VIEWER, allow_public=True)
    if not memorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memorial not found"
        )
    
    # --- Bulk-load all data for the tree (3 DB queries total) ---
    # BFS to discover all node IDs within max_depth
    all_ids: Set[int] = {memorial_id}
    frontier: Set[int] = {memorial_id}
    depth_map: Dict[int, int] = {memorial_id: 0}

    while frontier:
        rels_batch = db.query(FamilyRelationship).filter(
            FamilyRelationship.memorial_id.in_(frontier)
        ).all()
        new_ids: Set[int] = set()
        for rel in rels_batch:
            if rel.related_memorial_id not in all_ids:
                new_depth = depth_map[rel.memorial_id] + 1
                if new_depth <= max_depth:
                    new_ids.add(rel.related_memorial_id)
                    depth_map[rel.related_memorial_id] = new_depth
        all_ids.update(new_ids)
        frontier = new_ids

    memorials_map: Dict[int, Memorial] = {
        m.id: m for m in db.query(Memorial).filter(Memorial.id.in_(all_ids)).all()
    }
    all_rels = db.query(FamilyRelationship).filter(
        FamilyRelationship.memorial_id.in_(all_ids)
    ).all()

    children_map: Dict[int, List[int]] = defaultdict(list)
    spouse_map: Dict[int, List[int]] = defaultdict(list)
    for rel in all_rels:
        if rel.relationship_type == RelationshipType.CHILD:
            # memorial_id is parent, related_memorial_id is child
            children_map[rel.memorial_id].append(rel.related_memorial_id)
        elif rel.relationship_type == RelationshipType.PARENT:
            # memorial_id is child, related_memorial_id is parent → parent has memorial as child
            children_map[rel.related_memorial_id].append(rel.memorial_id)
        elif rel.relationship_type == RelationshipType.SPOUSE:
            spouse_map[rel.memorial_id].append(rel.related_memorial_id)

    def build_tree(node_id: int, depth: int, visited: Set[int]) -> Optional[FamilyTreeNode]:
        if depth > max_depth or node_id in visited:
            return None
        visited = visited | {node_id}

        m = memorials_map.get(node_id)
        if not m:
            return None

        children = []
        for child_id in children_map.get(node_id, []):
            child_node = build_tree(child_id, depth + 1, visited)
            if child_node:
                children.append(child_node)

        spouses = []
        for spouse_id in spouse_map.get(node_id, []):
            sm = memorials_map.get(spouse_id)
            if sm:
                spouses.append(FamilyTreeNode(
                    memorial_id=sm.id,
                    name=sm.name,
                    birth_date=sm.birth_date,
                    death_date=sm.death_date,
                    relationship_type=RelationshipType.SPOUSE,
                    cover_photo_id=sm.cover_photo_id,
                    children=[],
                    spouses=[]
                ))

        return FamilyTreeNode(
            memorial_id=m.id,
            name=m.name,
            birth_date=m.birth_date,
            death_date=m.death_date,
            cover_photo_id=m.cover_photo_id,
            children=children,
            spouses=spouses
        )

    def count_nodes(node: FamilyTreeNode) -> int:
        count = 1
        for child in node.children:
            count += count_nodes(child)
        for spouse in node.spouses:
            count += 1
        return count

    root = build_tree(memorial_id, 0, set())
    if not root:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to build family tree"
        )
    
    total_nodes = count_nodes(root)

    return FamilyTreeResponse(
        root=root,
        total_nodes=total_nodes
    )


@router.get("/memorials/{memorial_id}/full-tree", response_model=FullFamilyTreeResponse)
async def get_full_family_tree(
    memorial_id: int,
    max_depth: int = Query(6, ge=1, le=10),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Полный граф семьи: предки (generation < 0), потомки (generation > 0),
    выбранный человек (generation = 0). BFS по всему графу связей.
    """
    memorial = require_memorial_access(memorial_id, current_user, db, min_role=UserRole.VIEWER, allow_public=True)
    if not memorial:
        raise HTTPException(status_code=404, detail="Memorial not found")

    # Load all relationships once
    all_rels = db.query(FamilyRelationship).all()

    # Build undirected adjacency: node_id → [(neighbor_id, rel_type)]
    adj: Dict[int, List[tuple]] = defaultdict(list)
    for rel in all_rels:
        adj[rel.memorial_id].append((rel.related_memorial_id, rel.relationship_type.value))

    # BFS with generation tracking
    # generation rules: CHILD of X → X is at gen-1 relative to X's child
    # i.e. if we walk edge (A→B, type=parent): B is parent of A, so B.gen = A.gen - 1
    # if we walk edge (A→B, type=child): B is child of A, so B.gen = A.gen + 1
    # SPOUSE/SIBLING: same generation
    generation: Dict[int, int] = {memorial_id: 0}
    visited: Set[int] = {memorial_id}
    queue = [memorial_id]

    while queue:
        current = queue.pop(0)
        cur_gen = generation[current]
        for neighbor_id, rel_type in adj.get(current, []):
            if neighbor_id in visited:
                continue
            if rel_type == "parent":
                # current has a parent = neighbor → neighbor is one gen above
                neighbor_gen = cur_gen - 1
            elif rel_type == "child":
                # current has a child = neighbor → neighbor is one gen below
                neighbor_gen = cur_gen + 1
            else:
                # spouse / sibling → same generation
                neighbor_gen = cur_gen
            if abs(neighbor_gen) <= max_depth:
                generation[neighbor_id] = neighbor_gen
                visited.add(neighbor_id)
                queue.append(neighbor_id)

    node_ids = set(generation.keys())

    # Bulk-load memorials
    memorials_map: Dict[int, Memorial] = {
        m.id: m for m in db.query(Memorial).filter(Memorial.id.in_(node_ids)).all()
    }

    # Build nodes
    nodes = []
    for mid in node_ids:
        m = memorials_map.get(mid)
        if not m:
            continue
        nodes.append(FullTreeNode(
            memorial_id=m.id,
            name=m.name,
            birth_year=m.birth_date.year if m.birth_date else None,
            death_year=m.death_date.year if m.death_date else None,
            cover_photo_id=m.cover_photo_id,
            generation=generation[mid],
        ))

    # Build edges (only between nodes in the graph, deduplicate)
    seen_edges: Set[tuple] = set()
    edges = []
    for rel in all_rels:
        if rel.memorial_id in node_ids and rel.related_memorial_id in node_ids:
            key = (min(rel.memorial_id, rel.related_memorial_id),
                   max(rel.memorial_id, rel.related_memorial_id),
                   rel.relationship_type.value)
            if key not in seen_edges:
                seen_edges.add(key)
                edges.append(FullTreeEdge(
                    source=rel.memorial_id,
                    target=rel.related_memorial_id,
                    type=rel.relationship_type.value,
                    label=rel.custom_label if rel.relationship_type.value == 'custom' else None,
                ))

    return FullFamilyTreeResponse(nodes=nodes, edges=edges, root_id=memorial_id)


REL_LABELS = {
    "parent": "родитель",
    "child": "ребёнок",
    "spouse": "супруг/супруга",
    "sibling": "брат/сестра",
}

REL_LABELS_REVERSE = {
    "parent": "ребёнок",
    "child": "родитель",
    "spouse": "супруг/супруга",
    "sibling": "брат/сестра",
}


@router.get("/memorials/{memorial_id}/hidden-connections", response_model=HiddenConnectionsResponse)
async def get_hidden_connections(
    memorial_id: int,
    max_depth: int = Query(6, ge=2, le=10),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Найти все родственные связи (прямые и скрытые) через BFS по всему графу.

    Возвращает:
    - direct: прямые связи (1 хоп)
    - hidden: неочевидные связи (2+ хопов) — например, троюродные через смену фамилии
    """
    memorial = require_memorial_access(memorial_id, current_user, db, min_role=UserRole.VIEWER, allow_public=True)
    if not memorial:
        raise HTTPException(status_code=404, detail="Memorial not found")

    # Загружаем все связи одним запросом (нужны оба направления)
    all_rels = db.query(FamilyRelationship).all()

    # Строим неориентированный граф: node_id → [(neighbor_id, rel_type, direction)]
    graph: Dict[int, List[tuple]] = defaultdict(list)
    for rel in all_rels:
        graph[rel.memorial_id].append((rel.related_memorial_id, rel.relationship_type.value, "forward"))
        graph[rel.related_memorial_id].append((rel.memorial_id, rel.relationship_type.value, "reverse"))

    # BFS: для каждого узла храним путь ConnectionStep[]
    visited: Dict[int, List[ConnectionStep]] = {memorial_id: []}
    queue: List[int] = [memorial_id]
    all_names: Dict[int, str] = {memorial.id: memorial.name}

    while queue:
        current = queue.pop(0)
        current_path = visited[current]
        if len(current_path) >= max_depth:
            continue
        for neighbor_id, rel_type, direction in graph[current]:
            if neighbor_id in visited:
                continue
            label = REL_LABELS.get(rel_type, rel_type) if direction == "forward" else REL_LABELS_REVERSE.get(rel_type, rel_type)
            if neighbor_id not in all_names:
                m = db.query(Memorial.id, Memorial.name).filter(Memorial.id == neighbor_id).first()
                all_names[neighbor_id] = m.name if m else f"Мемориал #{neighbor_id}"
            step = ConnectionStep(
                memorial_id=current,
                name=all_names[current],
                relationship_label=label,
            )
            visited[neighbor_id] = current_path + [step]
            queue.append(neighbor_id)

    def _make_summary(path: List[ConnectionStep], target_name: str) -> str:
        if not path:
            return "прямая связь"
        parts = " → ".join(f"{s.name} ({s.relationship_label})" for s in path)
        return f"{parts} → {target_name}"

    direct: List[HiddenConnection] = []
    hidden: List[HiddenConnection] = []

    for node_id, path in visited.items():
        if node_id == memorial_id:
            continue
        hops = len(path)
        target_name = all_names.get(node_id, f"Мемориал #{node_id}")
        conn = HiddenConnection(
            target_memorial_id=node_id,
            target_name=target_name,
            path=path,
            hops=hops,
            connection_summary=_make_summary(path, target_name),
        )
        if hops == 1:
            direct.append(conn)
        else:
            hidden.append(conn)

    hidden.sort(key=lambda c: c.hops)
    return HiddenConnectionsResponse(hidden=hidden, direct=direct)


# Cluster island colors (cycling palette)
_CLUSTER_COLORS = [
    "#4A7C59",  # forest green  — Kelly
    "#5B7FA6",  # slate blue    — Anderson
    "#C0622E",  # terracotta    — Chang
    "#8E6BAB",  # purple        — Rossi
    "#B8963E",  # gold          — cluster 5
    "#3D8B8B",  # teal          — cluster 6
    "#A05070",  # mauve         — cluster 7
    "#607060",  # sage          — cluster 8
]

STRUCTURAL_TYPES = {"parent", "child", "spouse", "sibling",
                    "PARENT", "CHILD", "SPOUSE", "SIBLING"}


@router.get("/memorials/{memorial_id}/network-clusters", response_model=NetworkClustersResponse)
async def get_network_clusters(
    memorial_id: int,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Return family clusters (connected components via structural edges) and cross-cluster
    bridges (custom-type edges).  Used by the Family Network visualisation.
    """
    memorial = require_memorial_access(memorial_id, current_user, db, min_role=UserRole.VIEWER, allow_public=True)
    if not memorial:
        raise HTTPException(status_code=404, detail="Memorial not found")

    all_rels = db.query(FamilyRelationship).all()

    # Split into structural and custom edges
    structural: List[tuple] = []   # (a, b)
    custom_edges: List[FamilyRelationship] = []
    for rel in all_rels:
        if rel.relationship_type.value in STRUCTURAL_TYPES:
            structural.append((rel.memorial_id, rel.related_memorial_id))
        else:
            custom_edges.append(rel)

    # Collect all memorial IDs touched by any relationship
    all_ids: Set[int] = set()
    for a, b in structural:
        all_ids.add(a)
        all_ids.add(b)
    for rel in custom_edges:
        all_ids.add(rel.memorial_id)
        all_ids.add(rel.related_memorial_id)
    # Also include the focal memorial
    all_ids.add(memorial_id)

    # Build undirected adjacency for structural edges only
    struct_adj: Dict[int, Set[int]] = defaultdict(set)
    for a, b in structural:
        struct_adj[a].add(b)
        struct_adj[b].add(a)

    # Find connected components (clusters) via BFS
    component: Dict[int, int] = {}   # memorial_id → cluster_id
    cluster_idx = 0
    for start in sorted(all_ids):
        if start in component:
            continue
        queue = [start]
        component[start] = cluster_idx
        while queue:
            cur = queue.pop(0)
            for nb in struct_adj.get(cur, []):
                if nb not in component:
                    component[nb] = cluster_idx
                    queue.append(nb)
        cluster_idx += 1

    focal_cluster_id = component.get(memorial_id, 0)

    # Bulk-load all memorials in all_ids
    memorials_map: Dict[int, Memorial] = {
        m.id: m for m in db.query(Memorial).filter(Memorial.id.in_(all_ids)).all()
    }

    # Build cluster objects
    cluster_members: Dict[int, List[NetworkClusterMember]] = defaultdict(list)
    for mid, cid in sorted(component.items()):
        m = memorials_map.get(mid)
        if not m:
            continue
        cluster_members[cid].append(NetworkClusterMember(
            memorial_id=m.id,
            name=m.name,
            birth_year=m.birth_date.year if m.birth_date else None,
            death_year=m.death_date.year if m.death_date else None,
            cover_photo_id=m.cover_photo_id,
            is_alive=m.death_date is None,
        ))

    def _cluster_label(cid: int) -> str:
        members = cluster_members.get(cid, [])
        # derive label from last alphabetic word of each name (surname heuristic)
        import re
        surnames = []
        seen = set()
        for mem in members:
            # strip parenthetical maiden names like "(урожд. Попова)"
            clean = re.sub(r'\(.*?\)', '', mem.name).strip()
            words = [w for w in clean.split() if w.isalpha()]
            if words:
                sn = words[-1]
                if sn not in seen:
                    seen.add(sn)
                    surnames.append(sn)
        return " · ".join(surnames[:3]) or f"Cluster {cid + 1}"

    clusters = [
        NetworkCluster(
            cluster_id=cid,
            label=_cluster_label(cid),
            members=cluster_members[cid],
            color=_CLUSTER_COLORS[cid % len(_CLUSTER_COLORS)],
        )
        for cid in sorted(cluster_members.keys())
    ]

    # Build bridges (custom edges that cross cluster boundaries, deduplicated)
    seen_bridges: Set[tuple] = set()
    bridges: List[NetworkBridge] = []
    for rel in custom_edges:
        cid_a = component.get(rel.memorial_id)
        cid_b = component.get(rel.related_memorial_id)
        if cid_a is None or cid_b is None or cid_a == cid_b:
            continue
        key = (min(cid_a, cid_b), max(cid_a, cid_b),
               min(rel.memorial_id, rel.related_memorial_id),
               max(rel.memorial_id, rel.related_memorial_id))
        if key in seen_bridges:
            continue
        seen_bridges.add(key)
        src = memorials_map.get(rel.memorial_id)
        tgt = memorials_map.get(rel.related_memorial_id)
        bridges.append(NetworkBridge(
            source_cluster_id=cid_a,
            target_cluster_id=cid_b,
            source_memorial_id=rel.memorial_id,
            target_memorial_id=rel.related_memorial_id,
            source_name=src.name if src else f"#{rel.memorial_id}",
            target_name=tgt.name if tgt else f"#{rel.related_memorial_id}",
            label=rel.custom_label or "connection",
        ))

    return NetworkClustersResponse(
        clusters=clusters,
        bridges=bridges,
        focal_cluster_id=focal_cluster_id,
    )
