package examplefuncsplayer;

import battlehack17.*;

import java.util.stream.Stream;

public class RobotPlayer {
    public static void main(String[] args) throws Exception{
        BHLogger.setVerbosity(BHLogger.VERBOSITY_CHATTYDEV);
        Game game = new Game("testbot");
        game.waitForStart();
        while(!game.over()) {
            game.waitTillNextTurn();

            /* YOUR CODE HERE */

            Stream<EntityData> mybots = game.gameInfo.local.getMyEntities();
            Stream<EntityData> robots = mybots.filter(
                    (eachEntity)->eachEntity.isRobot()
            );
            robots.forEach((eachRobot)->handleRobot(eachRobot,game));

            /* DON'T PUT CODE AFTER HERE */

            if(game.gameInfo.myTurn())
                game.sendTurn();
        }

        BHLogger.log("Done!",BHLogger.VERBOSITY_OUTPUT);
    }

    /**
     * This code will handle the actions of a single robot.
     * @param robot The robot to handle
     * @param game The game (contains info on map and entities)
     */
    public static void handleRobot(EntityData robot, Game game) {
        if(!robot.canAct()) {
            // This robot can't act! We don't want to waste time on it.
            return;
        }
        for(Direction eachDirection: Direction.cardinalDirections) {
            // We access our local copy of the game info to determine if we control the
            // sectors around this robot.
            // The local copy might desync from the server (in theory, it won't)
            // But, it means that all our robots will have updated information on what
            // we THINK will happen.
            switch (game.gameInfo.local.controlArea(robot.location.add(eachDirection))) {
                case ALLY_CONTROLS_SECTOR:
                    break;
                case ENEMY_CONTROLS_SECTOR:
                    break;
                case NUETRAL_SECTOR:
                    if(robot.canBuild(eachDirection)) {
                        boolean buildWorked = robot.build(eachDirection);
                        // We built something!
                        if(buildWorked) {
                            return;
                        }
                        //If this didn't work, something must have gone wrong...
                    }
                    break;
                case NO_SECTOR:
                    break;
            }
        }

        // Okay, we didn't build any statues. Let's move towards the nearest enemy statue.

        // (Almost) All of Battlehacks iterables are provided to you via streams.
        // Streams are a feature of Java 1.8 that make manipulation of the iterable
        // really easy (compared to an array or list)

        // We'll start off by getting a stream of all the entities around this bot within throwing range
        // NOTE: One great thing about streams is that you can apply several functions
        Stream<EntityData> nearby = robot.nearbyEntities(Constants.THROW_TILE_DISTANCE);
        robot.build(Direction.NORTH,true);

    }
}
