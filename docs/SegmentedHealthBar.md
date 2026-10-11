# SegmentedHealthBar

An experimental MIT alternative in the `health-bars` category, available from
`school.zero.community:zero-community:0.1.3`. No alternative is recommended by
contributor metadata. Choose a plain HealthBar for continuous fill or this view
when visible boundaries help your app. Both use the same explicit update API.

```java
SegmentedHealthBar(int maximum)
SegmentedHealthBar(String caption, int maximum)
Node view()
void setHealth(int health)
int getHealth()
int getMaximum()
```

Create and update on the JavaFX application thread. The constructor starts full,
requires a positive maximum and non-null caption, and gives each instance its own
stable VBox view. `setHealth` clamps to zero through maximum and updates the
numeric label and accessible text. App code owns damage, healing and reset rules.

The view has `min(10, maximum)` segments. Boundaries use integer capacities as
close in size as possible, so every segment represents at least one health point.
Fill proceeds left to right; a segment may be partially filled. For maximum 13,
the capacities are 1, 1, 1, 2, 1, 1, 2, 1, 1, 2. At health 4, the first three
segments are full and the fourth is half full. No JavaFX properties, timer or
implicit state synchronization is required.

```java
import zero.community.SegmentedHealthBar;
SegmentedHealthBar energy = new SegmentedHealthBar("Energy", 13);
root.getChildren().add(energy.view());
energy.setHealth(4); // app-owned update
energy.setHealth(13); // explicit reset
```

[Adventure](../examples/segmented-adventure/Main.java) and
[study](../examples/segmented-study/Main.java) reuse the component with different
app-owned rules. Tests cover uneven capacities, small/large maxima, clamping,
reset, accessibility, stable independent views and useful constructor errors.
The class is experimental with no named maintainer; local checks cannot appoint
one or grant community acceptance, recommendation or core promotion.
