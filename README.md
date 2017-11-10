# BATTLECODE HACKATHON
Welcome to the battlecode hackathon!

## 1-minute setup:
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

## Bigger overview

## Specs

## API docs

## Other languages
- Java:
    - Follow the above instructions to start the viewer and server (don't start the python player)
    - Create a Java project wherever you'd like. Import battlehack17.jar into your project.
    - Copy RobotPlayer.java to get yourself started. You'll need a main function, with a game loop.
    - To run, use your IDE
    - When you're ready to submit, use your IDE to generate a jar containing both the extracted contents of battlehack17.jar, as well as your code. Mark your main class in the jar's manifest (your IDE will give you an option to do so). Then, modify run.sh and replace your_package_name.jar with the jar file's name.
    - IntelliJ version: File > Project Structure > Artifacts > JAR (remember to select where your main() is!)
    - Win all the glory!
- Other:
    Technically, we support other languages, but you'll have to do a lot more work to use any of them.
    Talk to the devs for more information.
