# BATTLECODE HACKATHON
Welcome to the battlecode hackathon!

## 1-minute setup (Python):
- Download a copy of this repository [here](https://github.com/battlecode/hackathon-starter/) or fork / clone it.
- Install a recent version of [node.js](https://nodejs.org/en/) (> 8). If you already have Node installed, you can check which version you have with `node --version` in your terminal.
- Open a terminal / command prompt.
- Run `npm install -g @battlecode/battlehack`.
    - If you're on linux, you might need `sudo`.
- Run `battlehack start` and leave that terminal running. Make sure that `http://localhost:8080/` has opened in your browser.
- Open a new terminal; `cd` into the [`hackathon-starter/python`](https://github.com/battlecode/hackathon-starter/tree/master/python/) directory and run `python player.py`.
- Open a third and last terminal; `cd` into the [`hackathon-starter/python`](https://github.com/battlecode/hackathon-starter/tree/master/python/) directory and run `python player.py` again.
- You should now be able to watch a game run in your browser.
- Open `player.py` and start hacking!

Note: you should ignore `run.sh` for now.

## 1-minute setup (Java)
- Download a copy of this repository [here](https://github.com/battlecode/hackathon-starter/) or fork / clone it.
- Install a recent version of [node.js](https://nodejs.org/en/) (> 8). If you already have Node installed, you can check which version you have with `node --version` in your terminal.
- Open a terminal / command prompt.
- Run `npm install -g @battlecode/battlehack`.
    - If you're on linux, you might need `sudo`.
- Run `battlehack start` and leave that terminal running. Make sure that `http://localhost:8080/` has opened in your browser.
- Create a Java project wherever you'd like. Import `java/battlehack17.jar` into your project.
- Copy RobotPlayer.java to get yourself started. You'll need a main function, with a game loop.
- To run, use your IDE. Make sure you run your program twice so that the two copies can fight each other.
- You should now be able to watch a game run in your browser.
- Open RobotPlayer.java and start hacking!

Note: you should ignore `run.sh` for now.

## Specs
See website: http://battlehack.mit.edu/#/releases

## API docs
There is documentation for the Python API in `python/battlecode-docs.txt` and `python/battlecode-docs.html`.
There is documentation for the Java API in `python/battlecode-docs.txt` and `python/battlecode-docs.html`.

## Uploading to the matchmaking server
Note: the matchmaking server doesn't open until 2PM.

- Python:
    - Go into the `python` directory.
    - Make sure that `run.sh` runs your main player.
    - Run `battlehack upload` and answer the prompts.
    - Win all the glory!
    
- Java:
    - When you're ready to submit, use your IDE to generate a jar containing both the extracted contents of battlehack17.jar, as well as your code. Mark your main class in the jar's manifest (your IDE will give you an option to do so).
    - IntelliJ version: File > Project Structure > Artifacts > JAR (remember to select where your main() is!)
    - Put `run.sh` and `your_package_name.jar` in the same directory.
    - Modify `run.sh` and replace `your_package_name.jar` with the jar file's name.
    - Go into the directory with `run.sh` and `your_package_name.jar` and answer the prompts.
    - Win all the glory!

## Other languages
Technically, we support other languages besides python 2, python 3, and java, but you'll have to do a lot more work to use any of them. Talk to the devs for more information.

## Source code
The source code for the competition is at https://github.com/battlecode/battlecode-hackathon. Feel free to peruse it.