"""
API endpoints для работы с семейными связями и родословной.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Set, Optional
from collections import defaultdict
from sqlalchemy import and_, or_

from app.db import get_db
from app.models import Memorial, FamilyRelationship, RelationshipType
from app.schemas import (
    FamilyRelationshipCreate,
    FamilyRelationshipResponse,
    FamilyTreeResponse,
    FamilyTreeNode,
)

router = APIRouter(prefix="/family", tags=["family"])


@router.post("/memorials/{memorial_id}/relationships", response_model=FamilyRelationshipResponse, status_code=status.HTTP_201_CREATED)
async def create_relationship(
    memorial_id: int,
    relationship: FamilyRelationshipCreate,
    db: Session = Depends(get_db),
):
    """
    Создать семейную связь между мемориалами.
    
    Например:
    - memorial_id=1, related_memorial_id=2, relationship_type="parent" 
      означает: мемориал 2 является родителем мемориала 1
    """
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
    
    # Создание связи
    db_relationship = FamilyRelationship(
        memorial_id=memorial_id,
        related_memorial_id=relationship.related_memorial_id,
        relationship_type=relationship.relationship_type,
        notes=relationship.notes
    )
    db.add(db_relationship)
    
    # Автоматическое создание обратной связи для некоторых типов
    if relationship.relationship_type == RelationshipType.PARENT:
        # Если A - родитель B, то B - ребенок A
        reverse_relationship = FamilyRelationship(
            memorial_id=relationship.related_memorial_id,
            related_memorial_id=memorial_id,
            relationship_type=RelationshipType.CHILD,
            notes=relationship.notes
        )
        db.add(reverse_relationship)
    elif relationship.relationship_type == RelationshipType.CHILD:
        # Если A - ребенок B, то B - родитель A
        reverse_relationship = FamilyRelationship(
            memorial_id=relationship.related_memorial_id,
            related_memorial_id=memorial_id,
            relationship_type=RelationshipType.PARENT,
            notes=relationship.notes
        )
        db.add(reverse_relationship)
    elif relationship.relationship_type == RelationshipType.SPOUSE:
        # Если A - супруг B, то B - супруг A (симметричная связь)
        reverse_relationship = FamilyRelationship(
            memorial_id=relationship.related_memorial_id,
            related_memorial_id=memorial_id,
            relationship_type=RelationshipType.SPOUSE,
            notes=relationship.notes
        )
        db.add(reverse_relationship)
    elif relationship.relationship_type == RelationshipType.SIBLING:
        # Если A - брат/сестра B, то B - брат/сестра A (симметричная связь)
        reverse_relationship = FamilyRelationship(
            memorial_id=relationship.related_memorial_id,
            related_memorial_id=memorial_id,
            relationship_type=RelationshipType.SIBLING,
            notes=relationship.notes
        )
        db.add(reverse_relationship)
    
    db.commit()
    db.refresh(db_relationship)
    
    return FamilyRelationshipResponse(
        id=db_relationship.id,
        memorial_id=db_relationship.memorial_id,
        related_memorial_id=db_relationship.related_memorial_id,
        relationship_type=db_relationship.relationship_type,
        notes=db_relationship.notes,
        related_memorial_name=related_memorial.name,
        created_at=db_relationship.created_at
    )


@router.get("/memorials/{memorial_id}/relationships", response_model=List[FamilyRelationshipResponse])
async def get_relationships(
    memorial_id: int,
    relationship_type: Optional[RelationshipType] = None,
    db: Session = Depends(get_db),
):
    """
    Получить все семейные связи мемориала.
    
    Query параметры:
    - relationship_type: фильтр по типу связи (parent, child, spouse, sibling)
    """
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
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
    
    # Получаем имена связанных мемориалов
    result = []
    for rel in relationships:
        related = db.query(Memorial).filter(Memorial.id == rel.related_memorial_id).first()
        result.append(FamilyRelationshipResponse(
            id=rel.id,
            memorial_id=rel.memorial_id,
            related_memorial_id=rel.related_memorial_id,
            relationship_type=rel.relationship_type,
            notes=rel.notes,
            related_memorial_name=related.name if related else None,
            created_at=rel.created_at
        ))
    
    return result


@router.delete("/relationships/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relationship(
    relationship_id: int,
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
    
    # Удаление обратной связи
    reverse_type = None
    if relationship.relationship_type == RelationshipType.PARENT:
        reverse_type = RelationshipType.CHILD
    elif relationship.relationship_type == RelationshipType.CHILD:
        reverse_type = RelationshipType.PARENT
    elif relationship.relationship_type in [RelationshipType.SPOUSE, RelationshipType.SIBLING]:
        reverse_type = relationship.relationship_type  # Симметричные связи
    
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
    db: Session = Depends(get_db),
):
    """
    Получить семейное дерево мемориала.
    
    Query параметры:
    - max_depth: максимальная глубина дерева (по умолчанию 3)
    """
    memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
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
        if rel.relationship_type == RelationshipType.PARENT:
            children_map[rel.memorial_id].append(rel.related_memorial_id)
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

