# Research Report

## blessed.lib

### Summary of Work

I was researching how to create an animated display in the terminal that responds to player input. I found that blessed was a useful tool to use. I created a little program that runs and responds to player input. Copilot helped me figure out how to use blessed.

### Motivation

Our project will use this research on the UI for our project. We needed a way to have the game run and respond in the terminal.

### Time Spent

I spent about 60 minutes looking through different Python libraries that would work for our project, and about 90 minutes playing around and working with the different libraries to see how they work.

### Results

I installed Blessed using the command:

```bash 
py -m pip install blessed
```

At the top of the program I start by importing the Terminal class from the blessed library:

```python
from blessed import Terminal
```

Then using that import I create a Terminal control object:

```python
term = Terminal()
```

This allows for the program to access Screen and Input features. Then we start the program by clearing the screen and hiding the cursor.

```python
print(term.clear + term.hide_cursor, end="", flush=True)
```

After we setup the terminal, we are now ready to run the program. To take in inputs, we need to use the line:

```python
with term.cbreak(), term.raw():
```

This enables immidate key input and raw key sequences. Then when determining which keys to use, we use the function:

```python
key = term.inkey()
```

Here is an example code:

```python
key = term.inkey(timeout=0.05)  # Read one key press from the terminal (non-blocking with timeout).
if key.code == term.KEY_UP:  # Compare pressed key code to terminal's Up Arrow constant.
    bird_y = max(0, bird_y - 1)
elif key.code == term.KEY_DOWN:  # Compare to terminal's Down Arrow constant.
    bird_y = min(HEIGHT - 1, bird_y + 1)
elif key.code == term.KEY_LEFT:  # Compare to terminal's Left Arrow constant.
    bird_x = max(0, bird_x - 1)
elif key.code == term.KEY_RIGHT:  # Compare to terminal's Right Arrow constant.
    bird_x = min(WIDTH - 1, bird_x + 1)
elif key == "\x1b":  # ESC
    break
```

This code takes in input using `term.inkey()` and then checks that code using `key.code` and compared it to blessed's library of different key inputs. Attached is a blessed resource document which has all of the key inputs.

One thing to note is that __Letter Key__ inputs are done using something like this:
```python
if key and key.lower() == "w":
```

One last thing to note is that before drawing the new screen each time, make sure to do ```python term.home```, that way it moves the cursor to the top-left every time.


### Sources

<!--list your sources and link them to a footnote with the source url-->

- [blessed resources](https://blessed.readthedocs.io/en/latest/index.html)
- [blessed keyboard input](https://blessed.readthedocs.io/en/latest/keyboard.html)

