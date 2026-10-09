# Evaluation: rules coach

Run: 2026-10-09 01:01  

- cases: 30
- check_ok: 30
- gap_found: 21
- gap_total: 22
- gap_by_kind: {'wrong_logic': '4/5', 'half_finished': '5/5', 'syntax_error': '4/4', 'empty': '4/4', 'off_topic': '4/4'}
- hints_shown: 30
- hint_leaks: 5
- hint_leaks_level3: 3
- hints_level3: 4
- ai_replies: 0
- fallbacks: None
- median_seconds: 1.0

| # | lesson | kind | expect | got | check | gap | source | s |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | correct | pass | pass | ok |  | rules | 0.8 |
| 2 | 1 | wrong_logic | error | error | ok | NO | rules | 0.6 |
| 3 | 1 | half_finished | miss | miss | ok | yes | rules | 0.6 |
| 4 | 1 | syntax_error | error | error | ok | yes | rules | 0.6 |
| 5 | 1 | copied_reference | pass | pass | ok |  | rules | 0.8 |
| 6 | 1 | empty | miss | miss | ok | yes | rules | 0.7 |
| 7 | 1 | off_topic | error | error | ok | yes | rules | 0.7 |
| 8 | 2 | correct | pass | pass | ok |  | rules | 1.0 |
| 9 | 2 | wrong_logic | miss | miss | ok | yes | rules | 1.0 |
| 10 | 2 | half_finished | miss | miss | ok | yes | rules | 1.0 |
| 11 | 2 | syntax_error | error | error | ok | yes | rules | 1.0 |
| 12 | 2 | copied_reference | pass | pass | ok |  | rules | 1.1 |
| 13 | 2 | empty | miss | miss | ok | yes | rules | 1.0 |
| 14 | 2 | off_topic | error | error | ok | yes | rules | 2.2 |
| 15 | 3 | correct | pass | pass | ok |  | rules | 1.2 |
| 16 | 3 | wrong_logic | miss | miss | ok | yes | rules | 1.2 |
| 17 | 3 | half_finished | miss | miss | ok | yes | rules | 1.2 |
| 18 | 3 | syntax_error | error | error | ok | yes | rules | 1.1 |
| 19 | 3 | wrong_logic | error | error | ok | yes | rules | 1.1 |
| 20 | 3 | empty | miss | miss | ok | yes | rules | 1.0 |
| 21 | 3 | off_topic | error | error | ok | yes | rules | 1.0 |
| 22 | 4 | correct | pass | pass | ok |  | rules | 1.2 |
| 23 | 4 | wrong_logic | pass | pass | ok |  | rules | 0.9 |
| 24 | 4 | half_finished | miss | miss | ok | yes | rules | 1.0 |
| 25 | 4 | syntax_error | error | error | ok | yes | rules | 1.0 |
| 26 | 4 | copied_reference | pass | pass | ok |  | rules | 1.3 |
| 27 | 4 | empty | miss | miss | ok | yes | rules | 0.8 |
| 28 | 4 | off_topic | error | error | ok | yes | rules | 0.9 |
| 29 | 4 | half_finished | miss | miss | ok | yes | rules | 0.9 |
| 30 | 4 | wrong_logic | error | error | ok | yes | rules | 0.9 |

## Replies (for manual review)

**1 correct: tree with numbers**  
> First tree is in: x=4, z=-6. Next you will let the code do the repeating instead of typing each tree. +50 XP

**2 wrong_logic: x and z left as letters**  
> The code hit an error. x is not defined. Available commands: ground, tree, rock, house, sun, fog, random. Fix it and run again.
> hint 1: Remove the // at the start of the comment line and put numbers in place of x and z.

**3 half_finished: tree line still commented out**  
> The tree(...) line is still commented out with //, so it does not run. Delete the // at the start of the line.
> hint 1: Remove the // at the start of the comment line and put numbers in place of x and z.

**4 syntax_error: missing closing parenthesis**  
> The code hit an error. Syntax error: missing ) after argument list. A bracket, brace or quote may be missing or extra. Fix it and run again.
> hint 1: Remove the // at the start of the comment line and put numbers in place of x and z.

**5 copied_reference: reference solution pasted**  
> First tree is in: x=4, z=-6. Next you will let the code do the repeating instead of typing each tree. +50 XP

**6 empty: empty editor**  
> There are no trees in the scene. Add a line such as tree(4, -6);.
> hint 1: Remove the // at the start of the comment line and put numbers in place of x and z.
> hint 2 (LEAKS: matches solution pattern: 'tree(4'): For example tree(4, -6); puts the tree 4 units right and 6 units back.
> hint 3 (LEAKS: matches solution pattern: 'tree(4'): Full answer: write tree(4, -6); as a line, with the semicolon at the end.

**7 off_topic: browser code instead of scene commands**  
> The code hit an error. alert is not defined. Available commands: ground, tree, rock, house, sun, fog, random. Fix it and run again.
> hint 1: Remove the // at the start of the comment line and put numbers in place of x and z.

**8 correct: loop with 12 random trees**  
> The forest is up. A loop repeats the same job driven by a number; enemy waves and level generation in games work the same way. +50 XP

**9 wrong_logic: loop condition still i < 3**  
> The loop works but the scene has 3 trees, the goal is 12. Check how many turns it runs: the i < ... part.
> hint 1: The loop condition is i < 3, so it runs 3 times. Make that number bigger.

**10 half_finished: 12 trees typed by hand, no loop**  
> You have 12 trees, but you typed each one by hand. Let a for loop do it; asking for 300 trees tomorrow would be a one-number change.
> hint 1: The loop condition is i < 3, so it runs 3 times. Make that number bigger.

**11 syntax_error: missing parenthesis in for header**  
> The code hit an error. Syntax error: Unexpected token '{'. A bracket, brace or quote may be missing or extra. Fix it and run again.
> hint 1: The loop condition is i < 3, so it runs 3 times. Make that number bigger.

**12 copied_reference: 12 trees in a straight row**  
> You have 12 trees but they stand in a straight row. For a natural forest, spread z with random(-15, 15) too. The loop idea is down: enemy waves and level generation work the same way. +50 XP

**13 empty: empty editor**  
> The scene has 0 trees and no loop. Put a tree(...) inside for (let i = 0; i < 12; i++) { ... }.
> hint 1: The loop condition is i < 3, so it runs 3 times. Make that number bigger.
> hint 2: The trees all sit on z = 0, in one row. Spread both x and z with random(-15, 15).
> hint 3 (LEAKS: matches solution pattern: 'i < 12; i++) { tree('): Full answer: for (let i = 0; i < 12; i++) { tree(random(-15, 15), random(-15, 15)); }

**14 off_topic: endless loop**  
> The code hit an error. The code did not finish in 1.5 seconds. It may be an endless loop: does your while or for have an exit condition? Fix it and run again.
> hint 1: The loop condition is i < 3, so it runs 3 times. Make that number bigger.

**15 correct: low sun and haze**  
> Sunset is set. Light and fog are the two cheapest tools for mood in a game. In the last mission you will combine everything. +50 XP

**16 wrong_logic: sun still high**  
> sun(80) is still high. Go to 15 or lower for a sunset.
> hint 1: The light still looks like midday. If you have not written sun(...) yet, add it on a new line.

**17 half_finished: sun set, no fog**  
> The light looks good. Now add haze: fog(0.5); softens the distant trees.
> hint 1: The light still looks like midday. If you have not written sun(...) yet, add it on a new line.

**18 syntax_error: missing parenthesis on sun**  
> The code hit an error. Syntax error: missing ) after argument list. A bracket, brace or quote may be missing or extra. Fix it and run again.
> hint 1: The light still looks like midday. If you have not written sun(...) yet, add it on a new line.

**19 wrong_logic: fog amount out of range (5)**  
> The code hit an error. fog(): amount must be between 0 and 1, you gave 5. Fix it and run again.
> hint 1: The light still looks like midday. If you have not written sun(...) yet, add it on a new line.

**20 empty: empty editor**  
> The light is still at midday. Add sun(10); to bring the sun to the horizon.
> hint 1: The light still looks like midday. If you have not written sun(...) yet, add it on a new line.
> hint 2 (LEAKS: matches solution pattern: 'sun(1'): Write sun(10); and fog(0.5); below the loop.
> hint 3 (LEAKS: matches solution pattern: 'sun(1'): Full answer: add two lines: sun(10); and fog(0.5);

**21 off_topic: words instead of numbers**  
> The code hit an error. sun(): height must be a number, but got "low". Fix it and run again.
> hint 1: The light still looks like midday. If you have not written sun(...) yet, add it on a new line.

**22 correct: village with ring of houses**  
> Village complete. The houses are spread out nicely. The sunset mood suits the village. Using loops kept your code short. You finished the path. +50 XP Coming next Character movement Enemy behaviour Import your own model

**23 wrong_logic: two houses on top of each other**  
> Village complete. All the houses sit on one line, like a street. Try a ring or clusters for a more organic feel. Using loops kept your code short. You finished the path. +50 XP Coming next Character movement Enemy behaviour Import your own model

**24 half_finished: only one house**  
> The village is taking shape. Still missing: 1 more house(s).
> hint 1: Reuse the loop pattern from earlier missions: for (let i = 0; i < 8; i++) { tree(random(-15, 15), random(-15, 15)); }

**25 syntax_error: missing closing brace**  
> The code hit an error. Syntax error: Unexpected token ')'. A bracket, brace or quote may be missing or extra. Fix it and run again.
> hint 1: Reuse the loop pattern from earlier missions: for (let i = 0; i < 8; i++) { tree(random(-15, 15), random(-15, 15)); }

**26 copied_reference: coach example village pasted**  
> Village complete. The houses are spread out nicely. The sunset mood suits the village. Using loops kept your code short. You finished the path. +50 XP Coming next Character movement Enemy behaviour Import your own model

**27 empty: empty editor**  
> The village is taking shape. Still missing: 2 more house(s), 6 more tree(s), 3 more rock(s).
> hint 1: Reuse the loop pattern from earlier missions: for (let i = 0; i < 8; i++) { tree(random(-15, 15), random(-15, 15)); }
> hint 2: Same pattern for rocks: rock(random(-10, 10), random(-10, 10)); inside a loop.
> hint 3: Place houses by hand: house(-6, 2); and house(6, -3, 1.3);

**28 off_topic: house placed far outside the map**  
> The code hit an error. house(): x must be between -20 and 20, you gave 100. Fix it and run again.
> hint 1: Reuse the loop pattern from earlier missions: for (let i = 0; i < 8; i++) { tree(random(-15, 15), random(-15, 15)); }

**29 half_finished: houses and trees but no rocks**  
> The village is taking shape. Still missing: 3 more rock(s).
> hint 1: Reuse the loop pattern from earlier missions: for (let i = 0; i < 8; i++) { tree(random(-15, 15), random(-15, 15)); }

**30 wrong_logic: words as coordinates**  
> The code hit an error. house(): x must be a number, but got "left". Fix it and run again.
> hint 1: Reuse the loop pattern from earlier missions: for (let i = 0; i < 8; i++) { tree(random(-15, 15), random(-15, 15)); }
