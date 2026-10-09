# HealthBar API

`zero.community.HealthBar` is an ordinary object with an ordinary JavaFX view.
Create and update it on the JavaFX application thread. The app owns its rules
and state; call `setHealth` after changing that state. No update discovery,
component registry, reflection or component superclass is required.

```java
HealthBar health = new HealthBar("Energy", 100);
show(health.view());
health.setHealth(75);
```

| Public API | Behavior |
| --- | --- |
| `HealthBar(int maximum)` | Starts full with caption `Health`. Maximum must be positive. |
| `HealthBar(String caption, int maximum)` | Starts full with a non-null caption and positive maximum. |
| `Node view()` | Returns the same VBox containing a Label and ProgressBar. One parent per instance. |
| `void setHealth(int health)` | Clamps to `0..maximum`, updates label, fill and accessible text immediately. |
| `int getHealth()` | Returns the last clamped displayed value. |
| `int getMaximum()` | Returns the fixed positive maximum. |

Invalid maximum throws `IllegalArgumentException` with `Maximum health must be
positive.` A null caption throws `NullPointerException` with `Health caption must
not be null.` Empty captions are allowed. Updates do not animate or run app rules.

0.1.0 intentionally preserves the historical integer-division defect: partial
health has an empty fill despite a correct numeric label. 0.1.1 divides as a
double, so 75/100 displays 75% and 7/8 displays 87.5%. The constructors and public
methods stay unchanged. The release-cycle proof expects the old defect on
install/revert and the corrected fill after update. This is a local fixture,
not a recommendation to distribute a known faulty version.

0.1.2 preserves the fixed behavior and the same explicit API, adding public MIT
artifact packaging. Historical 0.1.0/0.1.1 fixtures remain unchanged.
