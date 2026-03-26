# Research Report

## Clearing Previous Screens in a Terminal UI

### Summary of Work

I researched how terminal screen clearing works in Python CLI applications so I could improve screen transitions in our game interface. I focused on ANSI escape sequences and terminal UI refresh behavior, especially how to clear the screen and move the cursor back to the home position before rendering a new screen. This research helped me confirm that using a shared clear-screen helper was an appropriate way to prevent leftover text and overlapping interface elements.

### Motivation

Our project uses a terminal-based interface, and when users move between screens such as the menu, rules page, game screen, and leaderboard, old output can remain visible if the screen is not properly reset. This makes the interface look cluttered and confusing. I needed to research a reliable way to clear the terminal between screen transitions so that each screen starts from a clean frame.

### Time Spent

~20 minutes reading about ANSI escape sequences for terminal screen control

~15 minutes reviewing examples of Python terminal screen clearing behavior

~10 minutes comparing the behavior of clear-screen approaches with our CLI flow

### Results

The main thing I learned is that terminal output can be reset using ANSI escape sequences. In particular, `\033` represents the escape character that begins an ANSI control sequence.[^1][^2] The sequence `[2J` means to clear the visible screen, and `[H` means to move the cursor to the home position at the top-left corner of the terminal.[^1][^2] When combined, `\033[2J\033[H` clears the screen and resets the cursor position so that the next screen can be drawn from a clean starting point.[^1][^2]

This was directly relevant to my implementation because I used `CLEAR_SCREEN = "\033[2J\033[H"` in the code and applied it through a shared `clear_screen()` helper. This made sure that when the user moves between the menu, rules screen, gameplay, and leaderboard, the previous screen output does not remain visible underneath the new one.

This research helped justify why a shared clear-screen helper was the right design choice for our CLI interface. Instead of clearing output separately in many different places, using one common escape sequence made screen transitions more consistent and reduced visual clutter. It also made the interface easier to understand because each screen starts in a clean state before new content is printed.

I also learned that terminal-clearing behavior can depend somewhat on the terminal environment, so ANSI escape sequences are a practical but terminal-dependent approach.[^2] Even so, this method is widely used in terminal applications and is appropriate for a simple Python CLI game where the goal is to refresh the visible interface cleanly between screens.[^1]

Overall, this research confirmed both the meaning of the escape sequence I used and the reason it works well for preventing old interface output from remaining on screen during navigation.

### Sources

- ANSI Escape Sequences reference[^1]
- Stack Overflow discussion on clearing the screen with escape sequences[^2]


[^1]: https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797
[^2]: https://stackoverflow.com/questions/37774983/clearing-the-screen-by-printing-a-character
