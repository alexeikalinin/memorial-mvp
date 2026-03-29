"""
Полный тест-сьют для всех типов семейных связей.
Проверяет:
  - Создание каждого типа связи
  - Автоматическое создание обратной связи (reverse logic)
  - Автоматическое удаление обратной связи при delete
  - Валидация CUSTOM типа (обязателен custom_label)
  - Защита от дубликатов для каждого типа
  - Защита от самосвязи
  - Поле custom_label в response
  - Логическая согласованность таблицы связей
"""
import pytest


# ── Helpers ────────────────────────────────────────────────────────────────

def mk_memorial(auth_client, name):
    resp = auth_client.post("/api/v1/memorials/", json={"name": name, "is_public": False})
    assert resp.status_code == 201, f"Create memorial '{name}' failed: {resp.json()}"
    return resp.json()


def add_rel(auth_client, from_id, to_id, rel_type, custom_label=None, notes=None):
    body = {"related_memorial_id": to_id, "relationship_type": rel_type}
    if custom_label is not None:
        body["custom_label"] = custom_label
    if notes is not None:
        body["notes"] = notes
    return auth_client.post(f"/api/v1/family/memorials/{from_id}/relationships", json=body)


def get_rels(auth_client, memorial_id):
    resp = auth_client.get(f"/api/v1/family/memorials/{memorial_id}/relationships")
    assert resp.status_code == 200
    return resp.json()


def has_rel(rels, to_id, rel_type):
    """Проверяет, что в списке связей есть связь нужного типа с нужным мемориалом."""
    return any(r["related_memorial_id"] == to_id and r["relationship_type"] == rel_type for r in rels)


# ══════════════════════════════════════════════════════════════════════════
# 1. БАЗОВЫЕ ТИПЫ — существуют с самого начала
# ══════════════════════════════════════════════════════════════════════════

class TestBasicTypes:

    def test_parent_creates_reverse_child(self, auth_client):
        """PARENT A→B автоматически создаёт CHILD B→A."""
        a = mk_memorial(auth_client, "Отец")
        b = mk_memorial(auth_client, "Дочь")
        resp = add_rel(auth_client, a["id"], b["id"], "parent")
        assert resp.status_code == 201
        assert resp.json()["relationship_type"] == "parent"
        # Обратная связь
        b_rels = get_rels(auth_client, b["id"])
        assert has_rel(b_rels, a["id"], "child"), "Reverse CHILD not created"

    def test_child_creates_reverse_parent(self, auth_client):
        """CHILD A→B автоматически создаёт PARENT B→A."""
        a = mk_memorial(auth_client, "Сын")
        b = mk_memorial(auth_client, "Мать")
        resp = add_rel(auth_client, a["id"], b["id"], "child")
        assert resp.status_code == 201
        b_rels = get_rels(auth_client, b["id"])
        assert has_rel(b_rels, a["id"], "parent"), "Reverse PARENT not created"

    def test_spouse_is_symmetric(self, auth_client):
        """SPOUSE A→B автоматически создаёт SPOUSE B→A."""
        a = mk_memorial(auth_client, "Муж")
        b = mk_memorial(auth_client, "Жена")
        resp = add_rel(auth_client, a["id"], b["id"], "spouse")
        assert resp.status_code == 201
        b_rels = get_rels(auth_client, b["id"])
        assert has_rel(b_rels, a["id"], "spouse"), "Reverse SPOUSE not created"

    def test_sibling_is_symmetric(self, auth_client):
        """SIBLING A→B автоматически создаёт SIBLING B→A."""
        a = mk_memorial(auth_client, "Брат")
        b = mk_memorial(auth_client, "Сестра")
        resp = add_rel(auth_client, a["id"], b["id"], "sibling")
        assert resp.status_code == 201
        b_rels = get_rels(auth_client, b["id"])
        assert has_rel(b_rels, a["id"], "sibling"), "Reverse SIBLING not created"


# ══════════════════════════════════════════════════════════════════════════
# 2. НОВЫЕ ТИПЫ — добавлены в текущей версии
# ══════════════════════════════════════════════════════════════════════════

class TestStepFamily:

    def test_step_parent_creates_reverse_step_child(self, auth_client):
        """STEP_PARENT A→B создаёт STEP_CHILD B→A."""
        a = mk_memorial(auth_client, "Отчим")
        b = mk_memorial(auth_client, "Пасынок")
        resp = add_rel(auth_client, a["id"], b["id"], "step_parent")
        assert resp.status_code == 201
        assert resp.json()["relationship_type"] == "step_parent"
        b_rels = get_rels(auth_client, b["id"])
        assert has_rel(b_rels, a["id"], "step_child"), "Reverse STEP_CHILD not created"

    def test_step_child_creates_reverse_step_parent(self, auth_client):
        """STEP_CHILD A→B создаёт STEP_PARENT B→A."""
        a = mk_memorial(auth_client, "Падчерица")
        b = mk_memorial(auth_client, "Мачеха")
        resp = add_rel(auth_client, a["id"], b["id"], "step_child")
        assert resp.status_code == 201
        b_rels = get_rels(auth_client, b["id"])
        assert has_rel(b_rels, a["id"], "step_parent"), "Reverse STEP_PARENT not created"

    def test_delete_step_parent_removes_reverse(self, auth_client):
        """Удаление STEP_PARENT автоматически удаляет STEP_CHILD."""
        a = mk_memorial(auth_client, "Отчим2")
        b = mk_memorial(auth_client, "Пасынок2")
        rel = add_rel(auth_client, a["id"], b["id"], "step_parent").json()
        # Обратная связь существует
        b_rels_before = get_rels(auth_client, b["id"])
        assert has_rel(b_rels_before, a["id"], "step_child")
        # Удаляем прямую
        del_resp = auth_client.delete(f"/api/v1/family/relationships/{rel['id']}")
        assert del_resp.status_code == 204
        # Обратная тоже удалена
        b_rels_after = get_rels(auth_client, b["id"])
        assert not has_rel(b_rels_after, a["id"], "step_child"), "Reverse STEP_CHILD not deleted"


class TestAdoptiveFamily:

    def test_adoptive_parent_creates_reverse_adoptive_child(self, auth_client):
        """ADOPTIVE_PARENT A→B создаёт ADOPTIVE_CHILD B→A."""
        a = mk_memorial(auth_client, "Усыновитель")
        b = mk_memorial(auth_client, "Усыновлённый")
        resp = add_rel(auth_client, a["id"], b["id"], "adoptive_parent")
        assert resp.status_code == 201
        assert resp.json()["relationship_type"] == "adoptive_parent"
        b_rels = get_rels(auth_client, b["id"])
        assert has_rel(b_rels, a["id"], "adoptive_child"), "Reverse ADOPTIVE_CHILD not created"

    def test_adoptive_child_creates_reverse_adoptive_parent(self, auth_client):
        """ADOPTIVE_CHILD A→B создаёт ADOPTIVE_PARENT B→A."""
        a = mk_memorial(auth_client, "Удочерённая")
        b = mk_memorial(auth_client, "Удочеритель")
        resp = add_rel(auth_client, a["id"], b["id"], "adoptive_child")
        assert resp.status_code == 201
        b_rels = get_rels(auth_client, b["id"])
        assert has_rel(b_rels, a["id"], "adoptive_parent"), "Reverse ADOPTIVE_PARENT not created"

    def test_delete_adoptive_parent_removes_reverse(self, auth_client):
        """Удаление ADOPTIVE_PARENT удаляет ADOPTIVE_CHILD."""
        a = mk_memorial(auth_client, "Усыновитель2")
        b = mk_memorial(auth_client, "Усыновлённый2")
        rel = add_rel(auth_client, a["id"], b["id"], "adoptive_parent").json()
        auth_client.delete(f"/api/v1/family/relationships/{rel['id']}")
        b_rels = get_rels(auth_client, b["id"])
        assert not has_rel(b_rels, a["id"], "adoptive_child"), "Reverse ADOPTIVE_CHILD not deleted"


class TestHalfSibling:

    def test_half_sibling_is_symmetric(self, auth_client):
        """HALF_SIBLING A→B создаёт HALF_SIBLING B→A."""
        a = mk_memorial(auth_client, "Иван (единокровный)")
        b = mk_memorial(auth_client, "Ольга (единокровная)")
        resp = add_rel(auth_client, a["id"], b["id"], "half_sibling")
        assert resp.status_code == 201
        assert resp.json()["relationship_type"] == "half_sibling"
        b_rels = get_rels(auth_client, b["id"])
        assert has_rel(b_rels, a["id"], "half_sibling"), "Reverse HALF_SIBLING not created"

    def test_delete_half_sibling_removes_reverse(self, auth_client):
        """Удаление HALF_SIBLING удаляет обратную HALF_SIBLING."""
        a = mk_memorial(auth_client, "Брат-единокровный")
        b = mk_memorial(auth_client, "Сестра-единокровная")
        rel = add_rel(auth_client, a["id"], b["id"], "half_sibling").json()
        auth_client.delete(f"/api/v1/family/relationships/{rel['id']}")
        b_rels = get_rels(auth_client, b["id"])
        assert not has_rel(b_rels, a["id"], "half_sibling"), "Reverse HALF_SIBLING not deleted"


class TestPartner:

    def test_partner_is_symmetric(self, auth_client):
        """PARTNER A→B создаёт PARTNER B→A."""
        a = mk_memorial(auth_client, "Партнёр 1")
        b = mk_memorial(auth_client, "Партнёр 2")
        resp = add_rel(auth_client, a["id"], b["id"], "partner")
        assert resp.status_code == 201
        assert resp.json()["relationship_type"] == "partner"
        b_rels = get_rels(auth_client, b["id"])
        assert has_rel(b_rels, a["id"], "partner"), "Reverse PARTNER not created"

    def test_delete_partner_removes_reverse(self, auth_client):
        """Удаление PARTNER удаляет обратную PARTNER."""
        a = mk_memorial(auth_client, "Партнёр А")
        b = mk_memorial(auth_client, "Партнёр Б")
        rel = add_rel(auth_client, a["id"], b["id"], "partner").json()
        auth_client.delete(f"/api/v1/family/relationships/{rel['id']}")
        b_rels = get_rels(auth_client, b["id"])
        assert not has_rel(b_rels, a["id"], "partner"), "Reverse PARTNER not deleted"


class TestExSpouse:

    def test_ex_spouse_is_symmetric(self, auth_client):
        """EX_SPOUSE A→B создаёт EX_SPOUSE B→A."""
        a = mk_memorial(auth_client, "Бывший муж")
        b = mk_memorial(auth_client, "Бывшая жена")
        resp = add_rel(auth_client, a["id"], b["id"], "ex_spouse")
        assert resp.status_code == 201
        assert resp.json()["relationship_type"] == "ex_spouse"
        b_rels = get_rels(auth_client, b["id"])
        assert has_rel(b_rels, a["id"], "ex_spouse"), "Reverse EX_SPOUSE not created"

    def test_delete_ex_spouse_removes_reverse(self, auth_client):
        """Удаление EX_SPOUSE удаляет обратную EX_SPOUSE."""
        a = mk_memorial(auth_client, "Бывший муж 2")
        b = mk_memorial(auth_client, "Бывшая жена 2")
        rel = add_rel(auth_client, a["id"], b["id"], "ex_spouse").json()
        auth_client.delete(f"/api/v1/family/relationships/{rel['id']}")
        b_rels = get_rels(auth_client, b["id"])
        assert not has_rel(b_rels, a["id"], "ex_spouse"), "Reverse EX_SPOUSE not deleted"


# ══════════════════════════════════════════════════════════════════════════
# 3. CUSTOM ТИП
# ══════════════════════════════════════════════════════════════════════════

class TestCustomType:

    def test_custom_requires_custom_label(self, auth_client):
        """CUSTOM без custom_label → 400."""
        a = mk_memorial(auth_client, "Крёстный отец")
        b = mk_memorial(auth_client, "Крестник")
        resp = add_rel(auth_client, a["id"], b["id"], "custom")
        assert resp.status_code == 400
        assert "custom_label" in resp.json()["detail"].lower()

    def test_custom_with_label_succeeds(self, auth_client):
        """CUSTOM с custom_label → 201, label сохраняется."""
        a = mk_memorial(auth_client, "Крёстный")
        b = mk_memorial(auth_client, "Крестница")
        resp = add_rel(auth_client, a["id"], b["id"], "custom", custom_label="Крёстный отец")
        assert resp.status_code == 201
        data = resp.json()
        assert data["relationship_type"] == "custom"
        assert data["custom_label"] == "Крёстный отец"

    def test_custom_no_reverse_created(self, auth_client):
        """CUSTOM не создаёт автоматическую обратную связь."""
        a = mk_memorial(auth_client, "Опекун")
        b = mk_memorial(auth_client, "Подопечный")
        add_rel(auth_client, a["id"], b["id"], "custom", custom_label="Опекун")
        b_rels = get_rels(auth_client, b["id"])
        # B не должен иметь автоматической обратной связи к A
        assert not any(r["related_memorial_id"] == a["id"] for r in b_rels), \
            "CUSTOM should not auto-create reverse"

    def test_custom_label_returned_in_list(self, auth_client):
        """custom_label присутствует при запросе списка связей."""
        a = mk_memorial(auth_client, "Учитель")
        b = mk_memorial(auth_client, "Ученик")
        add_rel(auth_client, a["id"], b["id"], "custom", custom_label="Учитель и наставник")
        rels = get_rels(auth_client, a["id"])
        custom_rels = [r for r in rels if r["relationship_type"] == "custom"]
        assert len(custom_rels) == 1
        assert custom_rels[0]["custom_label"] == "Учитель и наставник"

    def test_custom_label_max_length(self, auth_client):
        """custom_label > 100 символов → 422."""
        a = mk_memorial(auth_client, "A")
        b = mk_memorial(auth_client, "B")
        long_label = "x" * 101
        resp = add_rel(auth_client, a["id"], b["id"], "custom", custom_label=long_label)
        assert resp.status_code == 422


# ══════════════════════════════════════════════════════════════════════════
# 4. ЗАЩИТА ОТ ОШИБОК
# ══════════════════════════════════════════════════════════════════════════

class TestValidation:

    def test_self_relation_forbidden(self, auth_client):
        """Связь мемориала с самим собой → 400."""
        a = mk_memorial(auth_client, "Одиночка")
        resp = add_rel(auth_client, a["id"], a["id"], "parent")
        assert resp.status_code == 400

    def test_duplicate_same_type_forbidden(self, auth_client):
        """Повторная связь того же типа → 400."""
        a = mk_memorial(auth_client, "А1")
        b = mk_memorial(auth_client, "Б1")
        add_rel(auth_client, a["id"], b["id"], "spouse")
        resp = add_rel(auth_client, a["id"], b["id"], "spouse")
        assert resp.status_code == 400

    def test_different_types_between_same_pair_allowed(self, auth_client):
        """Два разных типа связи между одними мемориалами — допустимо."""
        a = mk_memorial(auth_client, "А2")
        b = mk_memorial(auth_client, "Б2")
        r1 = add_rel(auth_client, a["id"], b["id"], "sibling")
        r2 = add_rel(auth_client, a["id"], b["id"], "half_sibling")
        assert r1.status_code == 201
        assert r2.status_code == 201

    def test_invalid_type_returns_422(self, auth_client):
        """Несуществующий тип связи → 422."""
        a = mk_memorial(auth_client, "А3")
        b = mk_memorial(auth_client, "Б3")
        resp = add_rel(auth_client, a["id"], b["id"], "nonexistent_type")
        assert resp.status_code == 422

    def test_unknown_memorial_returns_404(self, auth_client):
        """Связь с несуществующим мемориалом → 404."""
        a = mk_memorial(auth_client, "А4")
        resp = add_rel(auth_client, a["id"], 999999, "parent")
        assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════════════════
# 5. ЛОГИЧЕСКАЯ СОГЛАСОВАННОСТЬ REVERSE-ЛОГИКИ
# ══════════════════════════════════════════════════════════════════════════

class TestReverseLogicConsistency:

    def test_parent_child_bidirectional_count(self, auth_client):
        """После создания PARENT: у родителя 1 связь CHILD, у ребёнка 1 связь PARENT."""
        p = mk_memorial(auth_client, "Папа")
        c = mk_memorial(auth_client, "Сын")
        add_rel(auth_client, p["id"], c["id"], "parent")

        p_rels = get_rels(auth_client, p["id"])
        c_rels = get_rels(auth_client, c["id"])

        assert len([r for r in p_rels if r["relationship_type"] == "parent"]) == 1
        assert len([r for r in c_rels if r["relationship_type"] == "child"]) == 1

    def test_no_duplicate_reverse_on_both_directions(self, auth_client):
        """Если добавить PARENT A→B, то CHILD B→A уже есть — повторное добавление CHILD не дублирует."""
        a = mk_memorial(auth_client, "Родитель-X")
        b = mk_memorial(auth_client, "Ребёнок-X")
        add_rel(auth_client, a["id"], b["id"], "parent")
        # Пробуем добавить обратную вручную
        resp = add_rel(auth_client, b["id"], a["id"], "child")
        assert resp.status_code == 400, "Duplicate reverse should be rejected"

    def test_step_parent_reverse_is_step_child_not_child(self, auth_client):
        """STEP_PARENT создаёт STEP_CHILD, а не CHILD."""
        a = mk_memorial(auth_client, "Отчим-проверка")
        b = mk_memorial(auth_client, "Пасынок-проверка")
        add_rel(auth_client, a["id"], b["id"], "step_parent")
        b_rels = get_rels(auth_client, b["id"])
        assert not has_rel(b_rels, a["id"], "child"), "STEP_PARENT must NOT create CHILD reverse"
        assert has_rel(b_rels, a["id"], "step_child"), "STEP_PARENT must create STEP_CHILD reverse"

    def test_adoptive_reverse_is_adoptive_not_biological(self, auth_client):
        """ADOPTIVE_PARENT создаёт ADOPTIVE_CHILD, а не CHILD."""
        a = mk_memorial(auth_client, "Усыновитель-X")
        b = mk_memorial(auth_client, "Усыновлённый-X")
        add_rel(auth_client, a["id"], b["id"], "adoptive_parent")
        b_rels = get_rels(auth_client, b["id"])
        assert not has_rel(b_rels, a["id"], "child"), "ADOPTIVE_PARENT must NOT create CHILD"
        assert has_rel(b_rels, a["id"], "adoptive_child"), "ADOPTIVE_PARENT must create ADOPTIVE_CHILD"

    def test_all_symmetric_types_create_reverse(self, auth_client):
        """Все симметричные типы создают обратную связь того же типа."""
        symmetric_types = ["spouse", "ex_spouse", "partner", "sibling", "half_sibling"]
        for rel_type in symmetric_types:
            a = mk_memorial(auth_client, f"A-{rel_type}")
            b = mk_memorial(auth_client, f"B-{rel_type}")
            add_rel(auth_client, a["id"], b["id"], rel_type)
            b_rels = get_rels(auth_client, b["id"])
            assert has_rel(b_rels, a["id"], rel_type), \
                f"Symmetric type '{rel_type}' did not create reverse"

    def test_all_asymmetric_types_create_correct_reverse(self, auth_client):
        """Все асимметричные типы создают правильную обратную связь."""
        pairs = [
            ("parent", "child"),
            ("child", "parent"),
            ("step_parent", "step_child"),
            ("step_child", "step_parent"),
            ("adoptive_parent", "adoptive_child"),
            ("adoptive_child", "adoptive_parent"),
        ]
        for forward, expected_reverse in pairs:
            a = mk_memorial(auth_client, f"A-{forward}")
            b = mk_memorial(auth_client, f"B-{forward}")
            add_rel(auth_client, a["id"], b["id"], forward)
            b_rels = get_rels(auth_client, b["id"])
            assert has_rel(b_rels, a["id"], expected_reverse), \
                f"Type '{forward}' should create reverse '{expected_reverse}', not found"


# ══════════════════════════════════════════════════════════════════════════
# 6. УДАЛЕНИЕ — ПОЛНАЯ МАТРИЦА
# ══════════════════════════════════════════════════════════════════════════

class TestDeleteReverseMatrix:

    @pytest.mark.parametrize("forward,expected_reverse", [
        ("parent",          "child"),
        ("child",           "parent"),
        ("spouse",          "spouse"),
        ("sibling",         "sibling"),
        ("step_parent",     "step_child"),
        ("step_child",      "step_parent"),
        ("adoptive_parent", "adoptive_child"),
        ("adoptive_child",  "adoptive_parent"),
        ("half_sibling",    "half_sibling"),
        ("partner",         "partner"),
        ("ex_spouse",       "ex_spouse"),
    ])
    def test_delete_removes_reverse(self, auth_client, forward, expected_reverse):
        """Удаление связи типа {forward} удаляет обратную {expected_reverse}."""
        a = mk_memorial(auth_client, f"Del-A-{forward}")
        b = mk_memorial(auth_client, f"Del-B-{forward}")
        rel = add_rel(auth_client, a["id"], b["id"], forward).json()

        # Убедились, что обратная создана
        b_rels_before = get_rels(auth_client, b["id"])
        assert has_rel(b_rels_before, a["id"], expected_reverse), \
            f"Reverse '{expected_reverse}' was not created before delete"

        # Удаляем прямую
        del_resp = auth_client.delete(f"/api/v1/family/relationships/{rel['id']}")
        assert del_resp.status_code == 204

        # Обратная тоже исчезла
        b_rels_after = get_rels(auth_client, b["id"])
        assert not has_rel(b_rels_after, a["id"], expected_reverse), \
            f"Reverse '{expected_reverse}' was NOT deleted after deleting '{forward}'"

    def test_custom_delete_no_reverse_to_remove(self, auth_client):
        """Удаление CUSTOM не падает (нет обратной для удаления)."""
        a = mk_memorial(auth_client, "Del-Custom-A")
        b = mk_memorial(auth_client, "Del-Custom-B")
        rel = add_rel(auth_client, a["id"], b["id"], "custom", custom_label="Наставник").json()
        del_resp = auth_client.delete(f"/api/v1/family/relationships/{rel['id']}")
        assert del_resp.status_code == 204


# ══════════════════════════════════════════════════════════════════════════
# 7. ПОЛНОЕ ДЕРЕВО — все типы видны в /full-tree
# ══════════════════════════════════════════════════════════════════════════

class TestFullTree:

    def test_full_tree_includes_all_added_nodes(self, auth_client):
        """full-tree содержит все связанные мемориалы."""
        root = mk_memorial(auth_client, "Корень дерева")
        spouse = mk_memorial(auth_client, "Супруга корня")
        child = mk_memorial(auth_client, "Биологический ребёнок")
        step_child = mk_memorial(auth_client, "Пасынок")
        adoptive = mk_memorial(auth_client, "Приёмный ребёнок")

        add_rel(auth_client, root["id"], spouse["id"], "spouse")
        add_rel(auth_client, root["id"], child["id"], "parent")
        add_rel(auth_client, root["id"], step_child["id"], "step_parent")
        add_rel(auth_client, root["id"], adoptive["id"], "adoptive_parent")

        resp = auth_client.get(f"/api/v1/family/memorials/{root['id']}/full-tree")
        assert resp.status_code == 200
        data = resp.json()
        node_ids = {n["memorial_id"] for n in data["nodes"]}
        assert root["id"] in node_ids
        assert spouse["id"] in node_ids
        assert child["id"] in node_ids
        assert step_child["id"] in node_ids
        assert adoptive["id"] in node_ids

    def test_full_tree_edge_types_present(self, auth_client):
        """Рёбра full-tree содержат все добавленные типы."""
        root = mk_memorial(auth_client, "Корень-рёбра")
        partner = mk_memorial(auth_client, "Партнёр-рёбра")
        ex = mk_memorial(auth_client, "Бывший-рёбра")
        half = mk_memorial(auth_client, "Единокровный-рёбра")

        add_rel(auth_client, root["id"], partner["id"], "partner")
        add_rel(auth_client, root["id"], ex["id"], "ex_spouse")
        add_rel(auth_client, root["id"], half["id"], "half_sibling")

        resp = auth_client.get(f"/api/v1/family/memorials/{root['id']}/full-tree")
        assert resp.status_code == 200
        edge_types = {e["type"] for e in resp.json()["edges"]}
        assert "partner" in edge_types
        assert "ex_spouse" in edge_types
        assert "half_sibling" in edge_types
