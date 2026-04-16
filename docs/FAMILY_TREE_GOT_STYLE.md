# GOT-Style Family Tree — Архитектура и ключевые решения

> Документ описывает текущую реализацию generation-layout режима в `FamilyTree.jsx`.
> При возникновении багов используй скилл `/fix-family-tree`.

## Ключевые файлы

| Файл | Роль |
|------|------|
| `frontend/src/components/FamilyTree.jsx` | Рендер, стейт, переключение режимов |
| `frontend/src/components/FamilyTree.css` | Стили circle-нод, свечей, колец |
| `frontend/src/utils/familyTreeGenerationLayout.js` | Layout-движок: юниты, поколения, авто-экс-спаус |
| `frontend/src/utils/familyTreeOrthogonalConnectors.js` | SVG линии: брак, родитель→ребёнок, autoExSet |
| `frontend/src/utils/familyTreeScope.js` | filterGraphToScope, FAMILY_CONFIG, stub-ноды |

---

## Константы (FamilyTree.jsx)

```js
NODE_W = 90   // ширина ноды
NODE_H = 148  // высота: 4 (padding-top) + 80 (avatar) + 4 + 28 (name) + 14 (years) + 14 (rel) + 4
INTER_GEN_GAP = 56   // вертикальный зазор между поколениями
SUB_ROW_GAP   = 32   // зазор между подстроками одного поколения
```

**Компоненты высоты NODE_H:**
- `top: 4` — отступ аватара от верха ноды (чтобы `box-shadow` кольцо не обрезалось)
- `avatarSize = NODE_W - 10 = 80` — аватар квадратный (используется как круг)
- info block: `top: avatarSize + 8 = 88`
- имя: ~28px, годы: ~14px, метка-роль: ~14px, padding: 4px

---

## Аватар — критические inline-стили

```jsx
// В GenCircleNode и GenStubNode:
style={{
  width: avatarSize,
  height: avatarSize,
  left: avatarOffset,  // = (NODE_W - avatarSize) / 2 = 5
  top: 4,              // ← ОБЯЗАТЕЛЬНО: иначе box-shadow кольцо обрезается overflow:hidden
  boxShadow,
}}
```

```jsx
// Свечка (🕯) — outside avatar div, inline top:
style={{ left: avatarOffset + avatarSize - 20, top: avatarSize - 16 }}
//                                                    ↑ avatarSize - 20 + 4 (из-за top:4)

// Текстовый блок:
style={{ top: avatarSize + 8 }}
//                      ↑ avatarSize + 4 + 4 (offset)
```

---

## marriageBarY — линия брака

```js
// familyTreeOrthogonalConnectors.js
function marriageBarY(nodeY, nw) {
  const avatarH = nw - 10  // = 80
  // +4 компенсирует top:4 у аватара в JSX
  return nodeY + 4 + avatarH - 2  // = nodeY + 82
}
```

Брачная горизонталь рисуется на уровне почти-нижнего края аватара, **выше** текстового блока (который начинается с `nodeY + 88`).

---

## autoExSet — автоопределение бывших супругов

**Логика:** Если у человека 2+ супруга(и) и ВСЕ умерли → умерший РАНЬШЕ = предыдущий брак (💔, красноватая линия). Если кто-то жив → все умершие партнёры = бывшие.

```js
// Одинаковый алгоритм в двух местах:
// 1) familyTreeOrthogonalConnectors.js → buildOrthogonalConnectors()
// 2) familyTreeGenerationLayout.js → buildAutoExSet()
```

Результат `autoExSet` — Set строк `"minId|maxId"` (сравнение строковое).

---

## groupUnitsByRow — предотвращение пересечений линий

Дети от разных браков объединяются в одну подстроку через Union-Find:

```js
// Шаг 2 в groupUnitsByRow:
// Все дети одного родителя → в одну группу → одна подстрока → нет пересечений
```

Без этого Claire (от Robert+Linda) и Michael (от Robert+Patricia) попадали бы на разные подстроки, и линии пересекались.

---

## reorderGroupForExSpouse — порядок в строке

Расставляет ноды так: `[Patricia 💔 | Robert ♥ Linda]` — бывший супруг СЛЕВА от текущей пары.

```js
// Ищет: pair-юнит (Robert+Linda) + single-юнит (Patricia), связанные через autoExSet
// → вставляет single перед pair
```

---

## Цвета линий

| Тип | Цвет |
|-----|------|
| Текущий брак (родители→дети) | `rgba(196,168,130,0.75)` — золотистый |
| Предыдущий брак (autoExSet) | `rgba(180,110,100,0.70)` — красноватый |
| Кросс-семейный брак | `rgba(200, 175, 120, 0.95)` — золотой пунктир `7 5` |
| Обычный parent→child | `rgba(196,168,130,0.52)` |

---

## Скрытые семьи (unlock bar)

Кнопки "+ Anderson Family" и т.п. **скрыты в generation-mode** (`showGenerations = true`), т.к. multi-family layout в этом режиме не поддерживается:

```jsx
{!showGenerations && displayGraph?._lockedFamilies?.length > 0 && (
  <div className="ft-unlock-bar"> ... </div>
)}
```

Это сделано намеренно — multi-family mode работает только в pedigree-режиме.

---

## Умершие ноды

```css
.ft-circle-avatar--deceased {
  filter: brightness(0.58) saturate(0.55);
}
```

Условие: `!!memorial.death_year`. Свечка 🕯 добавляется снаружи аватар-дива (чтобы не обрезалась `overflow:hidden`).

---

## Метки ролей (Parent, Grandparent, etc.)

В `FamilyTree.jsx → buildRelLabels()`:
- edge type нормализуется в lowercase: `String(e.type || '').toLowerCase()`
- Fallback: `genDiffLabel(nodeId, rootGeneration, ...)` по разнице поколений

---

## Известные ограничения

- Multi-family + generation layout не поддерживается (unlock bar скрыт)
- `singleFamilyMode = visibleFamilies.length === 1` → центрирует колонку
- Patricia Ann Murphy Kelly (id=17) — супруга Robert, умерла раньше Linda → autoExSet помечает пару Robert+Patricia как ex-spouse
