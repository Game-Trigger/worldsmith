# Evaluation: ai coach

Run: 2026-10-09 15:04  

- cases: 30
- check_ok: 30
- gap_found: 19
- gap_total: 22
- gap_by_kind: {'wrong_logic': '4/5', 'half_finished': '5/5', 'syntax_error': '4/4', 'empty': '2/4', 'off_topic': '4/4'}
- hints_shown: 30
- hint_leaks: 3
- hint_leaks_level3: 2
- hints_level3: 4
- ai_replies: 26
- ai_hints: 24
- ai_hint_leaks: 0
- ai_gap_found: 16/19
- fallbacks: 4
- median_seconds: 1.35
- provider: gemini
- model: gemini-3.5-flash-lite
- requests: 59
- accepted_first_try: 44
- accepted_after_retry: 7
- gave_up_to_rules: 8
- model_replies_rejected: {'leak': 6, 'schema': 3, 'socratic': 3}
- prompt_tokens: 75412
- completion_tokens: 7021
- median_latency_ms: 1421

| # | lesson | kind | expect | got | check | gap | source | s |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | correct | pass | pass | ok |  | llm | 2.3 |
| 2 | 1 | wrong_logic | error | error | ok | yes | llm | 5.3 |
| 3 | 1 | half_finished | miss | miss | ok | yes | rules | 13.1 |
| 4 | 1 | syntax_error | error | error | ok | yes | llm | 2.0 |
| 5 | 1 | copied_reference | pass | pass | ok |  | llm | 0.1 |
| 6 | 1 | empty | miss | miss | ok | NO | llm | 1.1 |
| 7 | 1 | off_topic | error | error | ok | yes | llm | 1.2 |
| 8 | 2 | correct | pass | pass | ok |  | llm | 1.0 |
| 9 | 2 | wrong_logic | miss | miss | ok | NO | llm | 1.3 |
| 10 | 2 | half_finished | miss | miss | ok | yes | llm | 1.5 |
| 11 | 2 | syntax_error | error | error | ok | yes | llm | 1.3 |
| 12 | 2 | copied_reference | pass | pass | ok |  | llm | 1.3 |
| 13 | 2 | empty | miss | miss | ok | yes | llm | 1.4 |
| 14 | 2 | off_topic | error | error | ok | yes | llm | 6.1 |
| 15 | 3 | correct | pass | pass | ok |  | llm | 1.3 |
| 16 | 3 | wrong_logic | miss | miss | ok | yes | rules | 12.7 |
| 17 | 3 | half_finished | miss | miss | ok | yes | llm | 1.2 |
| 18 | 3 | syntax_error | error | error | ok | yes | llm | 1.3 |
| 19 | 3 | wrong_logic | error | error | ok | yes | llm | 1.7 |
| 20 | 3 | empty | miss | miss | ok | yes | llm | 1.3 |
| 21 | 3 | off_topic | error | error | ok | yes | rules | 0.5 |
| 22 | 4 | correct | pass | pass | ok |  | rules | 1.1 |
| 23 | 4 | wrong_logic | pass | pass | ok |  | llm | 1.4 |
| 24 | 4 | half_finished | miss | miss | ok | yes | llm | 1.3 |
| 25 | 4 | syntax_error | error | error | ok | yes | llm | 1.7 |
| 26 | 4 | copied_reference | pass | pass | ok |  | llm | 3.6 |
| 27 | 4 | empty | miss | miss | ok | NO | llm | 1.1 |
| 28 | 4 | off_topic | error | error | ok | yes | llm | 1.9 |
| 29 | 4 | half_finished | miss | miss | ok | yes | llm | 1.9 |
| 30 | 4 | wrong_logic | error | error | ok | yes | llm | 1.8 |

## Replies (for manual review)

**1 correct: tree with numbers**  
> Passed. You successfully planted your first tree at coordinates 4 and -6! How does adding a second tree nearby change the look of your landscape? +50 XP AI coach · gemini-3.5-flash-lite

**2 wrong_logic: x and z left as letters**  
> Not yet. Your code on line 2 uses letters x and z, but what numbers can you put there to place your tree on the ground? Missing concept: arguments need concrete numbers AI coach · gemini-3.5-flash-lite
> hint 1: What happens if you replace the letters x and z inside your tree function call with two numbers between negative twenty and twenty? Try replacing the letter x with a number like 4, and z with a number like negative 5 inside the parentheses. Missing concept: arguments need concrete numbers AI coach · gemini-3.5-flash-lite

**3 half_finished: tree line still commented out**  
> The tree(...) line is still commented out with //, so it does not run. Delete the // at the start of the line. Rule-based coach The AI coach took too long Try again
> hint 1: Remove the // at the start of the comment line and put numbers in place of x and z. Rule-based coach The AI coach took too long Try again

**4 syntax_error: missing closing parenthesis**  
> Not yet. Look at the end of line 2 in your code where you pass the numbers 4 and -6. What punctuation mark is sitting between them right now? Missing concept: argument separator AI coach · gemini-3.5-flash-lite
> hint 1: Let's look at the punctuation between 4 and -6 inside tree(4, -6;. Is a semicolon used to separate multiple numbers in a command? Check the punctuation mark right after the number 4 inside your tree command on line 2. Missing concept: arguments syntax AI coach · gemini-3.5-flash-lite

**5 copied_reference: reference solution pasted**  
> Passed. You successfully planted your first tree at coordinates 4 and -6! How does adding a second tree nearby change the look of your landscape? +50 XP AI coach · gemini-3.5-flash-lite

**6 empty: empty editor**  
> Not yet. Your code area is completely empty, so how can the program know where to place your first tree? Missing concept: A command call needs concrete numbers for its arguments. AI coach · gemini-3.5-flash-lite
> hint 1: Have you tried typing the name of the tree command in your editor yet? Look at the list of available commands and try typing the tree function on your blank line. Missing concept: Calling a function requires typing its name followed by parentheses containing numbers for its position. AI coach · gemini-3.5-flash-lite
> hint 2 (LEAKS: matches solution pattern: 'tree(4'): For example tree(4, -6); puts the tree 4 units right and 6 units back. Rule-based coach The AI coach cannot answer right now Try again
> hint 3 (LEAKS: matches solution pattern: 'tree(4'): Full answer: write tree(4, -6); as a line, with the semicolon at the end. Rule-based coach The AI coach cannot answer right now Try again

**7 off_topic: browser code instead of scene commands**  
> Not yet. Your code uses alert on line 2, which is not part of the scene commands. Do you remember which command you need to plant a tree? Missing concept: Using available scene commands instead of browser functions AI coach · gemini-3.5-flash-lite
> hint 1: Do you see where your code uses alert instead of the tree command? Where should you place the tree function call? Look at the list of allowed commands like tree(x, z). Try replacing the alert line with tree and give it two numbers for its coordinates. Missing concept: Function call syntax and scene commands AI coach · gemini-3.5-flash-lite

**8 correct: loop with 12 random trees**  
> Passed. You successfully used a for loop to place twelve trees scattered randomly across your world! How could you add a few rocks or a house among those trees to make the forest look even more natural? +50 XP AI coach · gemini-3.5-flash-lite

**9 wrong_logic: loop condition still i < 3**  
> Partly there. Your loop on line 2 only runs 3 times and places every tree at z = 0, so how could you change the loop limit and use i or random() to spread them out? Missing concept: The loop condition stops too early and all trees share the same z coordinate. AI coach · gemini-3.5-flash-lite
> hint 1: Look at your loop condition on line 2 and the z coordinate on line 3, what numbers should you change to reach twelve trees and spread them across the z axis? Check the number inside your loop condition where it checks i against 3, and see how the second argument in tree(x, z) always stays at 0. Missing concept: Loop count and z positioning AI coach · gemini-3.5-flash-lite

**10 half_finished: 12 trees typed by hand, no loop**  
> Partly there. You successfully placed 12 trees, but did you write them all on a single line instead of using a loop? Missing concept: Using a loop (for or while) to repeat tree creation instead of typing each one manually AI coach · gemini-3.5-flash-lite
> hint 1: Can you wrap those twelve tree commands inside a single for loop? Try writing for (let i = 0; i < 12; i++) { before your tree function and place your tree call inside the curly braces, using i to space them out. Missing concept: For loop AI coach · gemini-3.5-flash-lite

**11 syntax_error: missing parenthesis in for header**  
> Not yet. Look closely at the parentheses in your for loop on line 2. Is anything missing right before that opening curly brace? Missing concept: for loop syntax AI coach · gemini-3.5-flash-lite
> hint 1: Let's look at the opening parentheses and brackets on line 2. Is every opening parenthesis properly closed before your curly brace starts? Check the end of the loop condition on line 2. Every opening parenthesis like ( needs a matching closing parenthesis ) before you write {. Missing concept: Syntax error in loop header AI coach · gemini-3.5-flash-lite

**12 copied_reference: 12 trees in a straight row**  
> Passed. You successfully built your forest of 12 trees using a loop, but notice how they all line up perfectly straight along the z-axis at 0. How could you use random() for the second coordinate to make your trees scatter naturally across the landscape? +50 XP AI coach · gemini-3.5-flash-lite

**13 empty: empty editor**  
> Not yet. Your editor is completely empty and no trees have been planted yet. How can you write a for loop to place at least twelve trees? Missing concept: for loop AI coach · gemini-3.5-flash-lite
> hint 1: Let us start by setting up the repeat structure, so where should you type the keyword 'for' to begin counting your twelve trees? A for loop begins with 'for (let i = 0; i < N; i++)' followed by curly braces where you place your tree call. Missing concept: for loop structure AI coach · gemini-3.5-flash-lite
> hint 2: Can you see how to write the opening keyword 'for' followed by parentheses and curly braces to prepare your counting block? For example, to repeat an action three times, you would write 'for (let i = 0; i < 3; i++) { tree(i, 0); }' where the numbers inside control the loop. Missing concept: for loop syntax AI coach · gemini-3.5-flash-lite
> hint 3: Here is how a loop works in a different case: for (let i = 0; i < 5; i++) { rock(i, 0); }. Can you see how that structure repeats an action five times? To write a loop in your editor, start by typing the keyword 'for' followed by parentheses that set up your counter variable, its limit, and its step, with curly braces to hold your tree function. Missing concept: for loop syntax AI coach · gemini-3.5-flash-lite

**14 off_topic: endless loop**  
> Not yet. Your code stopped with a timeout because while (true) creates an endless loop that never finishes. What condition could you put inside the parentheses so the loop runs a specific number of times instead of running forever? Missing concept: While loop condition and infinite loop prevention AI coach · gemini-3.5-flash-lite
> hint 1: You removed the while loop, but how will you tell your new loop to run twelve times instead of three? Look at the condition part of your for loop on line 2. What number determines when the loop stops? Missing concept: for loop condition and count AI coach · gemini-3.5-flash-lite

**15 correct: low sun and haze**  
> Passed. You lowered the sun to 10 and added a soft fog of 0.5, which gives the forest a great morning glow. Can you think of how adding a few rocks could make the ground look even more natural? +50 XP AI coach · gemini-3.5-flash-lite

**16 wrong_logic: sun still high**  
> sun(80) is still high. Go to 15 or lower for a sunset. Rule-based coach The AI coach cannot answer right now Try again
> hint 1: Let's look at line 5 where your sunlight is set. What number is currently inside your sun function, and what number does the first goal ask you to use? Look at the number passed into your sun function. Overhead is 90 and the horizon is 0, so try replacing that 80 with a value of 15 or less. Missing concept: sun height AI coach · gemini-3.5-flash-lite

**17 half_finished: sun set, no fog**  
> Partly there. You successfully lowered the sun to 10, but what command is missing to add atmosphere to your forest? Missing concept: fog AI coach · gemini-3.5-flash-lite
> hint 1: You have your trees and a low sun, but which function creates that misty morning feeling? Take a look at the available functions in the introduction and find the one that takes an amount between 0 and 1 to control the haze. Missing concept: fog AI coach · gemini-3.5-flash-lite

**18 syntax_error: missing parenthesis on sun**  
> Not yet. It looks like there is a small syntax error on line 5 with a parenthesis. Can you check what punctuation is used to close your sun function call? Missing concept: syntax error AI coach · gemini-3.5-flash-lite
> hint 1: The light still looks like midday. If you have not written sun(...) yet, add it on a new line. Rule-based coach The AI coach cannot answer right now Try again

**19 wrong_logic: fog amount out of range (5)**  
> Not yet. Your sun call looks great, but what number range does the fog function accept on line 6? Missing concept: fog(amount) range AI coach · gemini-3.5-flash-lite
> hint 1: Look closely at the number you passed to fog() on line 6. What is the maximum allowed value for fog in this world? Check the upper limit for fog. While the sun function accepts numbers up to 90, fog only accepts amounts between 0 and 1. What happens if you change that 5 to a number less than 1? Missing concept: sun(height) and fog(amount) scale limits AI coach · gemini-3.5-flash-lite

**20 empty: empty editor**  
> Not yet. Your code is completely empty, so where should you place the sun and fog functions to start shaping the scene's mood? Missing concept: sun and fog functions AI coach · gemini-3.5-flash-lite
> hint 1: To set the mood with warm low light and atmosphere, which two functions do you need to add to your empty code? Check the available functions in the instructions for setting light angle and haze, and remember you also need to place at least eight trees in the scene. Missing concept: sun and fog AI coach · gemini-3.5-flash-lite
> hint 2: Here is how you might set an indoor light using a tiny lamp function: lamp(4). How can you use a similar function name to set the height of the sun in your editor? To bring in warm light and mist, type sun() with a number between 0 and 15 inside the parentheses, and add fog() with a number between 0.3 and 1 on the next line. Missing concept: sun and fog functions AI coach · gemini-3.5-flash-lite
> hint 3 (LEAKS: matches solution pattern: 'sun(1'): Full answer: add two lines: sun(10); and fog(0.5); Rule-based coach The AI coach cannot answer right now Try again

**21 off_topic: words instead of numbers**  
> The code hit an error. sun(): height must be a number, but got "low". Fix it and run again. Rule-based coach The AI coach cannot answer right now Try again
> hint 1: The light still looks like midday. If you have not written sun(...) yet, add it on a new line. Rule-based coach The AI coach cannot answer right now Try again

**22 correct: village with ring of houses**  
> Village complete. The houses are spread out nicely. The sunset mood suits the village. Using loops kept your code short. You finished the path. +50 XP Coming next Character movement Enemy behaviour Import your own model Rule-based coach The AI coach cannot answer right now Try again

**23 wrong_logic: two houses on top of each other**  
> Passed. You successfully placed all the required houses, trees, and rocks! Notice how your trees and rocks form straight horizontal lines along z equals 12 and minus 10; how might you vary their z positions to make them look more natural? +50 XP Coming next Character movement Enemy behaviour Import your own model AI coach · gemini-3.5-flash-lite

**24 half_finished: only one house**  
> Partly there. You have built plenty of trees and rocks, but how many houses does your village currently have? Missing concept: Not enough houses AI coach · gemini-3.5-flash-lite
> hint 1: Look at line 2 where you placed the house; how many house calls are currently in your code, and what number does the goal ask for? Check the goals list to see how many houses your village needs, and add another house call to reach that number. Missing concept: house count AI coach · gemini-3.5-flash-lite

**25 syntax_error: missing closing brace**  
> Not yet. It looks like a closing bracket or parenthesis is missing at the end of your code on line 6. Can you check where your loop's curly brace or parenthesis needs to close? Missing concept: syntax error AI coach · gemini-3.5-flash-lite
> hint 1: Let us look at line 4 where your loop starts. What punctuation is missing at the very end of your code on line 6? Check the end of your code block. Every opening parenthesis or brace needs a matching closing one to finish the statement and the loop. Missing concept: loops AI coach · gemini-3.5-flash-lite

**26 copied_reference: coach example village pasted**  
> Passed. You built a neat circular village with a ring of houses and a dense ring of trees surrounding the center! How could you adjust the rock loop in your code so the rocks don't all cluster in the middle? +50 XP Coming next Character movement Enemy behaviour Import your own model AI coach · gemini-3.5-flash-lite

**27 empty: empty editor**  
> Not yet. Your editor is completely empty right now, so none of the buildings or nature elements are showing up. Which function would you like to call first to place your very first object on the ground? Missing concept: object placement functions AI coach · gemini-3.5-flash-lite
> hint 1: Your editor is empty, so let us start by placing a house. Which function name should you type to place a house on the ground? Take a look at the available functions listed in your instructions, and try typing house(x, z) with two numbers inside the parentheses to choose its coordinates. Missing concept: object placement AI coach · gemini-3.5-flash-lite
> hint 2: Here is how you place a single rock at coordinates x=2 and z=5: rock(2, 5). Can you use that same idea to write your first house function call in your editor? To place an object, type the function name like house followed by parentheses containing your x and z coordinates, such as house(-3, 4). Missing concept: object placement functions AI coach · gemini-3.5-flash-lite
> hint 3: Let us break down the steps to start your village: how would you write a single function call to place a house? To place any object, type the function name followed by parentheses with your coordinates inside, like house(x, z). What coordinates will you choose for your first house? Missing concept: object placement syntax AI coach · gemini-3.5-flash-lite

**28 off_topic: house placed far outside the map**  
> Not yet. Your house on line 2 uses 100 for x, which is outside the allowed range of -20 to 20. Where on the ground should you place it instead? Missing concept: Coordinates must stay within the valid bounds of -20 to 20. AI coach · gemini-3.5-flash-lite
> hint 1: Remember that the ground only goes from -20 to 20. What numbers can you put inside house() to keep it on the screen? Check the numbers inside your house() call on line 2 and make sure they are between -20 and 20. Missing concept: Placement coordinates must stay within the valid range of -20 to 20 for x and z. AI coach · gemini-3.5-flash-lite

**29 half_finished: houses and trees but no rocks**  
> Partly there. You have your houses and a nice row of trees, but where are the rocks on your list and why are all eight trees stuck at z equals 12? Missing concept: adding rocks and varying the depth of trees AI coach · gemini-3.5-flash-lite
> hint 1: Let us add some boulders to the landscape. Which function should you call to place a rock in your scene? Take a look at how you placed your houses and trees on lines 2 and 4. Can you use that same approach to add rock(x, z) calls? Missing concept: rock placement AI coach · gemini-3.5-flash-lite

**30 wrong_logic: words as coordinates**  
> Not yet. Line 2 passes words like "left" into house(), but what type of value does the function expect for positions? Missing concept: numeric coordinates AI coach · gemini-3.5-flash-lite
> hint 1: Where should your single house live on the grid, and what numbers can you put inside house() to place it there? Check line 2 where you wrote house("left", "top"). Functions like house(x, z) need numbers between -20 and 20 for their coordinates instead of text words. Missing concept: numeric coordinates for placement AI coach · gemini-3.5-flash-lite
