import graphics   as gfx 
import state_enum as states
import apple      as appleFuncs

import projectile
import common
import player
import tiles
import aabb

from   state_enum             import STATE_PLAYING
from   state_playing_gameover import gameOverState

import random
import math
import time

def tryAddMoreApples(apples, elapsedTime, window):
    '''Adds apples'''
    notManyApples = len(apples) < (elapsedTime // 12) + 1
    if notManyApples:
        apples.append(appleFuncs.createRandomApple(window))


def playerFire(window, playerSprite, projectiles, projDirections, score):
    '''Tries to fire a player projectile if they click the mouse on the window'''
    fire, target = player.shouldFireProjectile(window)
    if fire and score > 0:
        playerPoint = playerSprite[1].getCenter()
        proj,    \
        velocity = projectile.create(playerPoint, target, window)
        projectiles.append(proj)
        projDirections.append(velocity)
        return True 
    return False

def updateApples(apples, playerMinX, isTilesActive, tileSprites, window):
    '''Update the updates, and test for collisions'''
    deltaLife = 0
    deltaScore = 0
    for apple in apples[:]:
        appleFuncs.moveApple(apple)
        if player.isTochingApple(apple, playerMinX):
            appleType = appleFuncs.radiusToAppleType(int(apple.getRadius()))
            if appleType == appleFuncs.REPAIR:
                tiles.repairTiles(tileSprites, isTilesActive, window)
            elif appleType == appleFuncs.BOOST:
                deltaLife += random.randint(1, 2)
            appleFuncs.removeApple(apples, apple)
            deltaScore += 1
        elif appleFuncs.isCollidingTile(apple, isTilesActive, tileSprites):
            appleFuncs.removeApple(apples, apple)
        elif appleFuncs.isOffScreen(apple):
            appleFuncs.removeApple(apples, apple)
            deltaLife -= 1
    return deltaLife, deltaScore

def createStatsDisplay(window):

    statsBG = gfx.Rectangle(gfx.Point(common.WINDOW_CENTER_X - 50, 25), gfx.Point(common.WINDOW_CENTER_X + 50, 125))
    statsBG.setFill("gray")
    scoreDisplay = gfx.Text(gfx.Point(common.WINDOW_CENTER_X, 50),  "Score: 0")
    livesDisplay = gfx.Text(gfx.Point(common.WINDOW_CENTER_X, 100), "Lives: 10")
    statsBG.draw(window)
    scoreDisplay.draw(window)
    livesDisplay.draw(window)

    return scoreDisplay, livesDisplay, [statsBG, scoreDisplay, livesDisplay]

def runMainGame(window, control):
    '''The main function handling the actual gameplay of the game'''
    #Draw background image
    #background = gfx.Image(gfx.Point(common.WINDOW_WIDTH//2, common.WINDOW_HEIGHT // 2), "../res/game_background.gif")
    #background.draw(window)

    #Set up score
    score = 0
    lives = 10
    scoreDisplay, livesDisplay, statSprites = createStatsDisplay(window)

    #Set up player
    playerXVel =   0.0
    playerAABB =   aabb.create(500.0, 500.0, 60.0, 45.0)
    playerSprite = player.createAndroid(window)

    #Create tiles
    tileSprites,  \
    isTilesActive = tiles.createTiles(window)
    NUM_TILES     = len(tileSprites)

    #Create apple list
    x = appleFuncs.getRandomAppleXPosition()
    apples = [appleFuncs.makeDefaultApple(x, 0, window)]

    projectiles = []
    projectilesDirections = []

    def updateScore(delta):
        nonlocal score
        score += delta 
        scoreDisplay.setText("Score: " + str(score))

    def updateLives(delta):
        nonlocal lives
        lives += delta
        livesDisplay.setText("Lives: " + str(lives))

    #Begin timer
    startTime = time.time()
    elapsed = 0
   
    isGamePaused = False
    gamePausedDisplay = common.createTitle("Paused - Press E to exit", y = tiles.BASE_HEIGHT / 2)

    #Main loop section for the playing state
    while lives > 0 and not common.shouldExit(window, control):
        #Create data for this frame
        elapsed = common.calculateTime(startTime)
        playerMinX = playerAABB["x"]
        playerMaxX = playerAABB["x"] + playerAABB["w"]
        key = common.getKeyPress(window)

        #Handle game pausing
        if key == "p":
            isGamePaused = not isGamePaused
            if isGamePaused:
                gamePausedDisplay.draw(window)
            else:
                gamePausedDisplay.undraw()


        if not isGamePaused:
            #Player input
            playerXVel = player.handleInput     (key, playerXVel)
            playerXVel = player.clampVelocity   (playerXVel)

            if (playerFire(window, playerSprite, projectiles, projectilesDirections, score)):
                updateScore(-1)

            #Fix for a glitch causing player to get stuck
            tileIndex = math.floor(playerSprite[1].getCenter().x / tiles.TILE_SIZE)
            if not isTilesActive[tileIndex]:
                isTilesActive[tileIndex] = True
                tileSprites[tileIndex].draw(window)

            #Update players, apples, and then projectiles
            playerXVel = player.tryCollideEdges(playerXVel, playerMinX, playerMaxX, isTilesActive)
            player.movePlayer(playerSprite, playerXVel)
            playerAABB["x"] += playerXVel
            
            tryAddMoreApples(apples, elapsed, window)
            deltaLives, deltaScore = updateApples(apples, playerMinX, 
                                                isTilesActive, tileSprites, window)
            updateScore(deltaScore)
            updateLives(deltaLives)

            projectile.update(projectiles, projectilesDirections, apples)
            
            common.redrawList(statSprites, window)
        else:
            if key == "e":
                break
            
        gfx.update(common.UPDATE_SPEED * 2)
    #end of the game (Game over)!
    #Undraw everything...
    common.undrawList(apples + projectiles + playerSprite + statSprites)
    tiles.undraw(tileSprites, isTilesActive)
    #...and return the results
    return score, elapsed


def runPlayState(window, control):
    '''Runs the main game'''
    while control["state"] == STATE_PLAYING and not common.shouldExit(window, control):
        score, elapsed = runMainGame(window, control)
        if common.shouldExit(window, control):
            return
        common.undrawAll(window)
        gameOverState(window, control, score, elapsed)
    
