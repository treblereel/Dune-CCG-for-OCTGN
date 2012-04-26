    # Python Scripts for the Dune CCG definition for OCTGN
    # Copyright (C) 2012  Konstantine Thoukydides

    # This python script is free software: you can redistribute it and/or modify
    # it under the terms of the GNU General Public License as published by
    # the Free Software Foundation, either version 3 of the License, or
    # (at your option) any later version.

    # This program is distributed in the hope that it will be useful,
    # but WITHOUT ANY WARRANTY; without even the implied warranty of
    # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    # GNU General Public License for more details.

    # You should have received a copy of the GNU General Public License
    # along with this script.  If not, see <http://www.gnu.org/licenses/>.

Solaris = ("Solaris", "b30701c1-d925-45fc-afe4-6c341a103f32")
Spice = ("Spice", "491cf29f-224c-4d8b-8e2d-58467686be88")
Favor = ("Favor", "6ed72fed-4a63-4f38-95bb-424cbbcdd427")
Deferment_Token = ("Deferment_Token", "f8f34145-60a8-4d2c-92e9-25824982944e")
Assembly = ("Imperial Assembly", "a5634dc5-ffd0-4428-95b5-13c6bb3ff00d")
Program = ("Program Token", "e66b8122-e98a-48bb-a9ba-991fde33d01c")

phases = [
    '{} is currently in the Pre-game Setup Phase'.format(me),
    "It is now Opening Interval. Disengage all cards then add Deferment Tokens and finally Assign Initiative",
    "It is now House Interval",
    "It is now Closing Interval. Perform Assembly Administration and then Hand Administration"]

#---------------------------------------------------------------------------
# Constants
#---------------------------------------------------------------------------

import re
import time

loud = 'loud' # So that I don't have to use the quotes all the time in my function calls
silent = 'silent' # Same as above
Xaxis = 'x'  # Same as above
Yaxis = 'y'	 # Same as above
DoesntDisengageColor = "#ffffff"


#---------------------------------------------------------------------------
# Global variables
#---------------------------------------------------------------------------

PLS = None # Stands for PLayerSide. Variable to keep track on which side each player is. 
playeraxis = None # Variable to keep track on which axis the player is
handsize = 7 # Used when automatically refilling your hand.
assemblysize = 3 # used when automatically refilling your assembly.
favorBought = 0
CHOAMDone = 0
DeployedDuneEvent = 0
DeployedImperiumEvent = 0
allegiances =['','','',''] # List to keep track of the player's allegiances.
totalevents = 0 # Variable to allow me to move events a bit to avoid hiding on top of exitisting ones.
totalprogs = 0 # Variable to allow me to move programs a bit to avoid hiding on top of exitisting ones.
totalholdings = 0
totalpersonas = 0
inactiveProgram = { }
assemblyCards = [ ]
#---------------------------------------------------------------------------
# General functions
#---------------------------------------------------------------------------

def num (s): 
# This function reads the value of a card and returns an integer. For some reason integer values of cards are not processed correctly
# see bug 373 https://octgn.16bugs.com/projects/3602/bugs/188805
# This function will also return 0 if a non-integer or an empty value is provided to it as it is required to avoid crashing your functions.
#   if s == '+*' or s == '*': return 0
   if not s: return 0
   try:
      return int(s)
   except ValueError:
      return 0

def chooseSide(): # Called from many functions to check if the player has chosen a side for this game.
   mute()
   global PLS, playeraxis
   if PLS == None:  # Has the player selected a side yet? If not, then...
      if table.isTwoSided():
         if me.hasInvertedTable():
            playeraxis = Yaxis
            PLS = -1
         else:
            playeraxis = Yaxis
            PLS = 1
      else:
         askside = askInteger("On which side do you want to setup?: 1 = Right, 2 = Left, 3 = Bottom, 4 = Top, 0 = None (All your cards will be put in the middle of the table and you'll have to arrange them yourself", 1) # Ask which axis they want,
         if askside == 1:
            playeraxis = Xaxis
            PLS = 1
         elif askside == 2:
            playeraxis = Xaxis
            PLS = -1
         elif askside == 3:
            playeraxis = Yaxis
            PLS = 1
         elif askside == 4:
            playeraxis = Yaxis
            PLS = -1
         else:
            playeraxis = None
            PLS = 0

def chkOut(globalvar): # A function which safely grabs a global variable by making sure nobody else is currently modifying it.
   retry = 0
   while getGlobalVariable(globalvar) == 'CHECKOUT':
      if retry == 2: 
         whisper("Global variable checkout failed after 3 tries. Another player must by doing something! Please try again later.")
         return 'ABORT'
      whisper("Global variable currently in use, retrying...")
      time.sleep(1)
      retry += 1
   globalVar = getGlobalVariable(globalvar)
   setGlobalVariable(globalvar, 'CHECKOUT')
   return globalVar
      
#---------------------------------------------------------------------------
# Card Placement functions
#---------------------------------------------------------------------------

def cwidth(card, divisor = 10):
# This function is used to always return the width of the card plus an offset that is based on the percentage of the width of the card used.
# The smaller the number given, the less the card is divided into pieces and thus the larger the offset added.
# For example if a card is 80px wide, a divisor of 4 will means that we will offset the card's size by 80/4 = 20.
# In other words, we will return 1 + 1/4 of the card width. 
# Thus, no matter what the size of the table and cards becomes, the distances used will be relatively the same.
# The default is to return an offset equal to 1/10 of the card width. A divisor of 0 means no offset.
   if divisor == 0: offset = 0
   else: offset = card.width() / divisor
   return (card.width() + offset)

def cheight(card, divisor = 10):
   if divisor == 0: offset = 0
   else: offset = card.height() / divisor
   return (card.height() + offset)

def yaxisMove(card, force = 'no'):
# Variable to move the cards played by player 2 on a 2-sided table, more towards their own side. 
# Player's 2 axis will fall one extra card length towards their side.
# This is because of bug #146 (https://github.com/kellyelton/OCTGN/issues/146)
   if me.hasInvertedTable() or (playeraxis == Yaxis and PLS == -1): cardmove = cheight(card)
   elif force == 'force': cardmove = -cheight(card)
   else: cardmove = 0
   return cardmove

def placeCard(card,type = None):
# This function automatically places a card on the table according to what type of card is being placed
# It is called by one of the various custom types and each type has a different value depending on if the player is on the X or Y axis.
   global totalprogs, totalholdings, totalpersonas
   if playeraxis == Xaxis:
      if type == 'SetupHomeworld':
         card.moveToTable(homeDistance(card), 0) # We move it to one side depending on what side the player chose.
      if type == 'SetupDune':
         card.moveToTable(homeDistance(card), cheight(card)* PLS) # We move it to one side depending on what side the player chose.
         card.isFaceUp = False
      if type == 'SetupProgram':          # We move them behind the homeworld
         card.moveToTable(homeDistance(card) - cardDistance(card) / 2 - (PLS * totalprogs * 20), 0)
         card.sendToBack()
         card.isFaceUp = False
         totalprogs += 1
      if type == 'PlayEvent': # Events are placed subdued
         card.moveToTable(homeDistance(card) + PLS * totalevents * 35, cheight(card)* -2 * PLS + PLS * totalevents * -35) 
         card.isFaceUp = False
      if type =='DeployHolding':
         card.moveToTable(homeDistance(card) - cardDistance(card), -cheight(card) * PLS + totalholdings * cheight(card)) # We move them just in front and to the side of the player's homeworld
         totalholdings += 1
         if totalholdings == 5: totalholdings = -4
      if type =='DeployPersona':
         card.moveToTable(homeDistance(card) - 2 * cardDistance(card), totalpersonas * cheight(card)) # We move them just ahead of the player's homeworld, as some distance.
         totalpersonas += 1
         if totalpersonas == 5: totalpersonas = -5
      if type =='DeployResource':
         card.moveToTable(cardDistance(card), cheight(card) * PLS) # We move it close to the table center, towards the player's side.
         card.sendToBack()
   elif playeraxis == Yaxis:
      if type == 'SetupHomeworld':
         card.moveToTable(0 ,homeDistance(card) - yaxisMove(card,'force')) 
      if type == 'SetupDune':
         card.moveToTable(cwidth(card)* PLS,homeDistance(card) - yaxisMove(card,'force')) 
         card.isFaceUp = False
      if type == 'SetupProgram': 
         card.moveToTable(0 ,homeDistance(card) - cardDistance(card) / 4 - (PLS * totalprogs * 30) - yaxisMove(card,'force'))
         card.sendToBack()
         card.isFaceUp = False
         totalprogs += 1
      if type == 'PlayEvent':
         card.moveToTable(cwidth(card)* -4 * PLS + PLS * totalevents * -35,homeDistance(card) + PLS * totalevents * 35 - yaxisMove(card)) 
         card.isFaceUp = False
      if type =='DeployHolding':
         card.moveToTable(-cwidth(card) * PLS + totalholdings * cheight(card), homeDistance(card) - cardDistance(card)) # We move them just in front and to the side of the player's homeworld
         totalholdings += 1
         if totalholdings == 7: totalholdings = -4
      if type =='DeployPersona':
         card.moveToTable(totalpersonas * cheight(card),homeDistance(card) - 2 * cardDistance(card)) # We move them just ahead of the player's homeworld, as some distance.
         totalpersonas += 1
         if totalpersonas == 7: totalpersonas = -5
      if type =='DeployResource':
         card.moveToTable(cwidth(card) * PLS,cardDistance(card)) # We move it close to the table center, towards the player's side.
         card.sendToBack()
   else: card.moveToTable(0,0)

def homeDistance(card):
# This function returns the distance from the middle each player's homeworld will be setup towards their PLS. 
# This makes the code more readable and allows me to tweak these values from one place
   if table.isTwoSided(): return (PLS * cheight(card) * 4) # players on an inverted table are placed half a card away from their edge.
   else:
      if playeraxis == Xaxis:
         return (PLS * cwidth(card) * 10) # players on the X axis, are placed 10 times a card's width towards their side (left or right)
      elif playeraxis == Yaxis:
         return (PLS * cheight(card) * 4 - yaxisMove(card)) # players on the Y axis, are placed 4 times a card's height towards their side (top or bottom)

def cardDistance(card):
# This function returns the size of the card towards a player's side. 
# This is useful when playing cards on the table, as you can always manipulate the location
#   by multiples of the card distance towards your side
# So for example, if a player is playing on the bottom side. This function will always return a positive cardheight.
#   Thus by adding this in a moveToTable's y integer, the card being placed will be moved towards your side by one multiple of card height
#   While if you remove it from the y integer, the card being placed will be moved towards the centre of the table by one multiple of card height.
   if playeraxis == Xaxis:
      return (PLS * cwidth(card))
   elif playeraxis == Yaxis:
      return (PLS * cheight(card))

#---------------------------------------------------------------------------
# Conditions Check General Functions
#---------------------------------------------------------------------------

def eventDeployTypeChk(subtype): # Check if the conditions to deploy an event are fulfilled
   global DeployedDuneEvent, DeployedImperiumEvent  
   if re.search(r'Imperium', subtype): # Imperium events can only be played if you control a homeworld, or Dune and only one per round per player.
      if Homeworlds() == 0:
         if not confirm("You're not allowed to deploy an Imperium Event without controlling a Homeworld . Bypass?"): 
            notify("{} is deploying an Imperium event, even though they control no Homeworld.".format(me))
            return 'NOK' 
      if DeployedImperiumEvent == 0: # If no Imperium event has been played this turn, just mark one as played and continue.
         DeployedImperiumEvent = 1
         return 'OK'
      elif confirm("You have already deployed one Imperium event this turn. Are you sure you are allowed to deploy another?"):
         return 'Extra' # If one has been played this turn, ask the player to confirm (in case they have a card effect) and continue or not accordingly.
      else: return 'NOK'
   elif re.search(r'Dune', subtype): # Dune events can only be played if you control a Dune fief, or Dune and only one per round per player.
      if DuneFiefs() == 0:
         if not confirm("You're not allowed to deploy a Dune Event without controlling a Dune fief. Bypass?"): 
            notify("{} is deploying a Dune event, even though they control no Dune fief.".format(me))
            return 'NOK' 
      if DeployedDuneEvent == 0:
         DeployedDuneEvent = 1
         return 'OK'
      elif confirm("You have already deployed one Dune event this turn. Are you sure you are allowed to deploy another?"):
         return 'Extra'
      else: return 'NOK'

def DuneFiefs(): # This function goes through your cards on the table and looks to see if you control any Dune Fiefs.
   DuneFiefsNR = 0
   myCards = (c for c in table
      if c.controller == me
      and c.isFaceUp
      and (re.search(r'Dune Fief', c.Subtype) or c.model == '2037f0a1-773d-42a9-a498-d0cf54e7a001')) # Dune itself is also a Dune Fief.
   for mycard in myCards: DuneFiefsNR += 1
   return DuneFiefsNR

def Homeworlds(): # This function goes through your cards on the table and looks to see if you control any Homeworlds.
   HomeNR = 0
   myCards = (c for c in table
      if c.controller == me
      and c.isFaceUp
      and (re.search(r'Homeworld', c.Subtype) or c.model == '2037f0a1-773d-42a9-a498-d0cf54e7a001')) # Dune itself is also a Homeworld.
   for mycard in myCards: HomeNR += 1
   return HomeNR


def noteAllegiances(): # This function checks every card in the Imperial Deck and makes a list of all the available allegiances.
   global allegiances # A global list that will containing all the allegiances existing in a player's deck.
   p = 1 # pointer for the list
   for card in me.piles['Imperial Deck']: 
      # Ugly hack follows. We need to move each card in the discard pile and then back into the deck because OCTGN won't let us peek at cards in facedown decks.
      card.moveTo(me.piles['Imperial Discard']) # Put the card in the discard pile in order to make its properties visible to us.
      if len(players) > 1: random = rnd(1,100) # Fix for multiplayer only. Makes Singleplayer setup very slow otherwise.
      if card.model == '2037f0a1-773d-42a9-a498-d0cf54e7a001':  # If the player moved dune put Dune by mistake to their Deck, move it to their hand to be placed automatically.
         card.moveTo(me.piles['Imperial Discard'])
         whisper("Dune found in your Imperial Deck. Discarding. Please remove Dune from your Imperial Deck during deck construction!")
         continue
      if card.Allegiance not in allegiances and card.Allegiance != 'None' and card.Allegiance != '': # If the allegiance is not neutral and not in our list already...
         allegiances[p] = card.Allegiance                                     # Then add it at the next available position
         p += 1
      card.moveToBottom(me.piles['Imperial Deck'])
   if chkAdversaries() != 'OK':
      notify("Faction Adversaries found within {}'s Deck. Deck seems to be illegal!".format(me))

def chkAdversaries(): # Check if there are any adversaties of factions in the Imperial deck. (Check page 4 of the ToT Rulebook.)
   global allegiances
   for allegiance in allegiances:
      if allegiance == 'The Fremen' and 'House Harkonnen' in allegiances: return 'conflict'
      elif allegiance == 'The Spacing Guild' and ('The Bene Gesserit Sisterhood' in allegiances or 'Dune Smugglers' in allegiances): return 'conflict'
      elif allegiance == 'House Atreides' and ('House Harkonnen' in allegiances or 'House Corrino' in allegiances): return 'conflict'
      elif allegiance == 'House Corrino' and 'House Atreides' in allegiances: return 'conflict'
      elif allegiance == 'House Harkonnen' and ('House Atreides' in allegiances or 'The Fremen' in allegiances): return 'conflict'
      elif allegiance == 'The Bene Gesserit Sisterhood' and 'The Spacing Guild' in allegiances: return 'conflict'
      elif allegiance == 'Dune Smugglers' and 'The Spacing Guild' in allegiances: return 'conflict'
      elif allegiance == 'The Spice Miners Guid' and 'The Water Sellers Union' in allegiances: return 'conflict'
      elif allegiance == 'The Water Sellers Union' and 'The Spice Miners Guid' in allegiances: return 'conflict'
   return 'OK'

#---------------------------------------------------------------------------
# Table group actions
#---------------------------------------------------------------------------

def nextPhase(group, x = 0, y = 0):  
# Function to take you to the next phase. 
   mute()
   if shared.Phase == 3: 
      shared.Phase = 1 # In case we're on the last phase (Closing Interval), go back to the first game phase (Opening Interval)
   else: shared.Phase += 1 # Otherwise, just move up one phase
   showCurrentPhase()

def goToOpening(group, x = 0, y = 0): # Go directly to the Opening Interval
   mute()
   shared.Phase = 1
   showCurrentPhase()

def goToHouse(group, x = 0, y = 0): # Go directly to the House Interval
   mute()
   shared.Phase = 2
   showCurrentPhase()

def goToClosing(group, x = 0, y = 0): # Go directly to the Closing Interval
   mute()
   shared.Phase = 3
   showCurrentPhase()


def showCurrentPhase(): # Just say a nice notification about which phase you're on.
   notify(phases[shared.Phase].format(me))

def goToSetup(group, x = 0, y = 0):  # Go back to the Pre-Game Setup phase.
# This phase is not rotated with the nextPhase function as it is a way to basically restart the game.
# It also serves as a control, so as to avoid a player by mistake using the setup function during play.
   global PLS, playeraxis, handsize, assemblysize, favorBought, CHOAMDone, DeployedDuneEvent, DeployedImperiumEvent, allegiances, totalevents, inactiveProgram
   mute()
   PLS = None
   playeraxis = None
   handsize = 7
   assemblysize = 3
   favorBought = 0
   CHOAMDone = 0
   DeployedDuneEvent = 0
   DeployedImperiumEvent = 0
   allegiances =['','','',''] # List to keep track of the player's allegiances.
   shared.Phase = 0
   me.Spice = 0
   me.Solaris = 5
   me.Favor = 10
   me.Initiative = 0
   totalevents = 0
   totalprogs = 0
   setGlobalVariable("petitionedCard", "Empty") # Clear the shared variables.
   setGlobalVariable("passedPlayers", "[]")
   setGlobalVariable("defeatedPlayers", "[]")
   inactiveProgram.clear() # Clear the dictionary for reuse.
   assemblyCards[:] = [] # Empty the list.
   showCurrentPhase() # Remind the players which phase it is now

def flipCoin(group, x = 0, y = 0):
    mute()
    n = rnd(1, 10)
    if n < 6:
        notify("{} flips heads.".format(me))
    else:
        notify("{} flips tails.".format(me))

def petition(card, x=0, y=0): # An almost superfluous function that basically redirects to subdue( ) or placeBid(). It's purpose is that I can have the same menu action on both cards and table context menus.
   cardID = chkOut("petitionedCard") # A quick grab of the shared peti
   if cardID == 'ABORT': return # Leave if someone is already using it.
   setGlobalVariable("petitionedCard", cardID)
   if cardID != 'Empty': placeBid(table) # If the player used this action and there's a currently petitioning card, we assume they just wanted to bid.
   elif card.markers[Assembly] == 0: whisper("You can only use this action on Imperial Assembly cards")
   else: subdue(card)


def placeBid(group, x = 0, y = 0):
# This function does the following:
#* It Checks to see if the player has passed in this petition already
#* It check if they are the last player standing in the bidding process and if so, declare them as the winner and take appropriate action, depending on if they are the owner or contestor
#* If they are not the winner, then they can increase their bid for this petition, or pass.
   mute()
   highestbid = 0 # Variable tracking what the highest bid is
   playersInBid = 0 # Variable tracking how many players are still in the bid
   overdraft = False # Variable tracking if the player tried to bid more than the Solaris in their Bank
   costZeroCard = False # A variable to track if the petitioned card has 0 deployment cost and take it into account during checks
   cardID = chkOut("petitionedCard") # Grab the card ID being petitioned.
   if cardID == 'ABORT': return # Leave if someone is already using it.
   elif cardID == 'Empty':
      whisper("No petition seems to be in progress. Please use this action on a face-down assembly card to start one first.")
      setGlobalVariable("petitionedCard", cardID) # If we're going to return before the end of the function, we need to checkin, or the next functions will fail.
      return
   else: card = Card(int(cardID)) # to make things easier and more readable.
   if num(card.properties['Deployment Cost']) == 0: costZeroCard = True
   for player in players: # Mark what the highest bid is and see how many players are currently still bidding
      if player.Bid > highestbid: highestbid = player.Bid
      if player.Bid > 0: playersInBid += 1
   if playersInBid == 0 and card.owner == me: playersInBid = 1
   if playersInBid == 1 and (me.Bid > 0 or costZeroCard): # If there's just one player remaining in the bid and it's the current player, then it means he's the "last man standing" so they are the winner of the petition
      if confirm("You seem to have won this petition, is this correct?"): # But lets just make sure just in case...
         if card.owner == me: # if we're the petitioner
            if card.allegiance == allegiances[0]: # if the card is of our own allegiance, we can reduce the cost via favor
               FavorLost = -1
               while FavorLost < 0 or FavorLost > highestbid: # This loop is to prevent the user from putting a value higher than the bid and thus gaining solaris.
                  FavorLost = askInteger("You have the house advantage for this petition and can use favor to reduce the final cost.\n\nHow much favor do you want to spend?\n(Max {})?".format(highestbid), 0)
                  if FavorLost == None: FavorLost = 0
                  if FavorLost > highestbid: whisper("You cannot reduce the deployment cost to negative")
               if me.Solaris < highestbid: # if we don't have enough money to pay the cost, we need to lose favor.
                  FavorLost = highestbid - me.Solaris
               me.Solaris -= highestbid - FavorLost
               me.Favor -= FavorLost
               if FavorLost > 0: extraText = " and {} favor".format(FavorLost)
               else: extraText = ''
            elif card.allegiance in allegiances: # If the card if not of our allegiance, but is of a secondary house we're using, we need to pay one favor extra.
               FavorLost = 1
               if me.Solaris < highestbid:
                  FavorLost += highestbid - me.Solaris
               me.Favor -= FavorLost
               me.Solaris -= highestbid - FavorLost
               extraText = " and lost {} favor".format(FavorLost)
            else: # If the card is netural, then there's nothing special.
               FavorLost = 0
               if me.Solaris < highestbid:
                  FavorLost += highestbid - me.Solaris
               me.Favor -= FavorLost
               me.Solaris -=highestbid
               if FavorLost > 0: extraText = " and lost {} favor".format(FavorLost)
               else: extraText = ''
            notify("{} has successfully petitioned for {} with a final bid of {}. They have spent {} solaris{} to pay the deployment cost.".format(me, card, highestbid, highestbid - FavorLost, extraText))
            card.markers[Assembly] = 0
            placeCard(card, "Deploy{}".format(card.Type)) # We deploy the card depending on its type.
            assemblyCards.remove(card) # Remove the deployed card from the list of assembly cards
            card.orientation = Rot90
         else: # If we're a contesting player...
            ContestCost = highestbid - num(card.properties['Deployment Cost'])
            FavorLost = 0
            if me.Solaris < ContestCost: # If we can't pay the full cost, we need to pay the rest with favor.
               FavorLost -= ContestCost - me.Solaris
               extraText = " and {} favor".format(FavorLost)
            else: extraText = ''
            me.Solaris -= ContestCost
            notify("{} has paid {} Solaris{} to contest the deployment of {}. The house of {} cannot call any more Petitions this turn".format(me, ContestCost, extraText, card, card.owner))
            time.sleep(1)
            card.isFaceUp = False
         setGlobalVariable("petitionedCard", "Empty") # Clear the shared variables for use in the next petition. Always need to do this before a return.
         setGlobalVariable("passedPlayers", "[]")
         me.Bid = 0
         return
   chkVar = chkOut("passedPlayers") # Checkout the passedPlayers global variable, which is a list with the player IDs of all the players who have passed on this petition.
   if chkVar == 'ABORT': return
   passedPL = eval(chkVar) # We grab the variable in string format and use the eval() to make it a list
   if me._id in passedPL: # See if the current player has passed already, and if so, warn them but give a chance to re-enter the bid (say because of card effects or wrongly pressing 0)
      if not confirm("You have already passed this petition. You are not normally allowed to bid a petition you have passed on the bid.\n\nBypass?"): return
      notify("{} has re-enterred the bidding contest".format(me))
      passedPL.remove(me._id)
   mybid = askInteger("What is your bid?\n\n[Currently highest bid is {} Solaris.]\n[Card Deployment Cost is {}].\n(Putting 0 will cancel the bid)".format(highestbid, card.properties['Deployment Cost']), 0)
   while 0 < mybid <= highestbid and highestbid > 0: 
      mybid = askInteger("You must bid higher then the current bid of {}. Please bid again.\n\n(0 will cancel the bid)".format(highestbid), 0)
      if mybid > me.Solaris: 
         if not confirm("You have bid more than your available Solaris in your bank. You're not normally allowed to do this, even if you would reduce it with favor.\n\nBypass?"): mybid = highestbid
         else: overdraft = True
   if mybid == 0 or mybid == None: 
      notify("{} has passed for this petition".format(me))
      passedPL.append(me._id)
      me.Bid = 0
   else:
      if overdraft: extraText = " by exceeding their banked Solaris"
      else: extraText =""
      notify("{} has increased the bid to {}{}".format(me, mybid,extraText))
      me.Bid = mybid
   setGlobalVariable("passedPlayers", str(passedPL))
   setGlobalVariable("petitionedCard", cardID)
   
#---------------------------------------------------------------------------
# Table card actions
#---------------------------------------------------------------------------

def inspectCard(card, x = 0, y = 0): # This function shows the player the card text, to allow for easy reading until High Quality scans are procured.
   confirm("{}".format(card.Operation))

def engage(card, x = 0, y = 0):
    mute()
    if not card.isFaceUp and card.markers[Assembly] == 1:
      subdue(card)
      return
    card.orientation ^= Rot90
    if card.orientation & Rot90 == Rot90:
        notify('{} engages {}'.format(me, card))
    else:
        notify('{} disengages {}'.format(me, card))

def dueling(card, x = 0, y = 0):
    mute()
    card.orientation ^= Rot90
    if card.orientation & Rot90 == Rot90:
        notify('{} declares a Dueling rite with {}'.format(me, card))
    else:
        notify('{} disengages {}'.format(me, card))

def battle(card, x = 0, y = 0):
    mute()
    card.orientation ^= Rot90
    if card.orientation & Rot90 == Rot90:
        notify('{} declares a Battle rite with {}'.format(me, card))
    else:
        notify('{} disengages {}'.format(me, card))

def arbitration(card, x = 0, y = 0):
    mute()
    card.orientation ^= Rot90
    if card.orientation & Rot90 == Rot90:
        notify('{} declares an Arbitration rite with {}'.format(me, card))
    else:
        notify('{} disengages {}'.format(me, card))

def intrigue(card, x = 0, y = 0):
    mute()
    card.orientation ^= Rot90
    if card.orientation & Rot90 == Rot90:
        notify('{} declares an Intrigue rite with  {}'.format(me, card))
    else:
        notify('{} disengages {}'.format(me, card))

def subdue(card, x = 0, y = 0):
    mute()
    faceup = 0
    if not card.isFaceUp: # Horrible hack until the devs can allow me to look at facedown card properties.
       card.isFaceUp = not card.isFaceUp  # Gah!
       snapshot = card
       name = card.name
       type = card.Type
       subtype = card.Subtype
       cost = num(card.properties['Deployment Cost']) 
       card.isFaceUp = not card.isFaceUp # GAH!
    if card.markers[Assembly] == 0:
        if card.isFaceUp:
            notify("{} subdues {}.".format(me, card))
            card.isFaceUp = False
        elif type == 'Event': # Events have special deployment rules
            if card.markers[Deferment_Token] < cost or card.markers[Deferment_Token] == 0:
                if confirm("Events cannot normally be played unless they have equal or more deferment tokens than their deployment cost and at least one. \n\nAre you sure you want to do this?"):
                    deployCHK = eventDeployTypeChk(subtype)
                    if deployCHK != 'NOK': # Check if there's been any other events of the same typed played this turn by this player.
                        card.isFaceUp = True
                        if deployCHK == 'OK': notify("{} deploys {} with {} deferment tokens.".format(me, card, card.markers[Deferment_Token]))
                        else: notify("{} deploys another {} event - {} with {} deferment tokens.".format(me, subtype, card, card.markers[Deferment_Token]))
            else: 
                deployCHK = eventDeployTypeChk(subtype)
                if deployCHK != 'NOK': # Check if there's been any other events of the same typed played this turn by this player.
                    card.isFaceUp = True
                    if deployCHK == 'OK': notify("{} deploys {} with {} deferment tokens.".format(me, card, card.markers[Deferment_Token]))
                    else: notify("{} deploys another {} event - {} with {} deferment tokens.".format(me, subtype, card, card.markers[Deferment_Token]))
        elif searchUniques(card, name, 'deploy') == 'NOK': return # Check if the card is unique and in the table. If so, abort this function.
        elif searchNatives(subtype) == 'NOK': return # Check if the card is a native persona and if there's any dune fiefs in our control. If so, abort this function after a confirm.
        elif card.markers[Deferment_Token] == 0 and cost > 0:
            if confirm("You cannot normally deploy cards with 0 deferment tokens. Bypass?"):
	            notify("{} deploys {} which had 0 deferment tokens.".format(me, card))   
	            card.isFaceUp = True
        elif card.markers[Deferment_Token] < cost:
            if confirm("Card has less deferment tokens than its deployment cost. Do you need to automatically pay the difference remaining from your treasury?"):
                if payCost(cost - card.markers[Deferment_Token]) == 'OK':
                    card.isFaceUp = True
                    notify("{} pays {} and deploys {}.".format(me, cost - card.markers[Deferment_Token], card))
                    card.markers[Deferment_Token] = 0
            elif confirm("Do you want to deploy the card at no cost instead?"):
                card.isFaceUp = True
                notify("{} deploys {} at no cost (Card had {} less deferment tokens than its deployment cost).".format(me, card, cost - card.markers[Deferment_Token]))
                card.markers[Deferment_Token] = 0            
        else:
            card.isFaceUp = True
            notify("{} deploys {}.".format(me, card))
            card.markers[Deferment_Token] = 0
            if re.search(r'Program', card.Subtype) and card.Type == 'Plan': inactiveProgram[card] = False
    else:
        chkVar = chkOut("petitionedCard")
        if chkVar == 'ABORT': return
        if card.isFaceUp:
            notify("{} has cancelled their petition.".format(me))
            card.isFaceUp = False
            setGlobalVariable("petitionedCard", "Empty")
            setGlobalVariable("passedPlayers", "[]")
        else:
            if chkVar != 'Empty': 
               whisper("Another petition (for {}) is currently in progress, please complete that one first.".format(Card(int(chkVar))))
               setGlobalVariable("petitionedCard", chkVar)
               return
            if me.Solaris < cost:
                if not confirm("You're not allowed to start a peition when you do not have at least as much solaris as the deployment cost of the card. \n\nAre you sure you want to proceed?"): return
            if searchNatives(subtype) == 'NOK': return
            if searchUniques(card, name, 'petition') == 'NOK': return
            initialBid = -1
            while initialBid < cost:
               initialBid = askInteger("What will your initial bid be? (Min {}). 0 will cancel the petition.".format(cost), cost)
               if (initialBid == 0 and cost != 0) or initialBid == None: return # If the player puts zero for the bid, or closes the window, abort.
            card.isFaceUp = True
            if card.Allegiance == allegiances[0]: # Position 0 is always the player's sponsor.
                notify("{} initiates a petition for {} with an initial bid of {}".format(me, card, initialBid))
                #whisper("This card is of your sponsor's allegiance. Remember that if you win the petition. you may opt to reduce its cost by 1 solaris for each favor you discard")
            elif card.Allegiance in allegiances: notify("{} initiates a petition for {} with an initial bid of {}.".format(me, card, initialBid))
            else: notify("{} initiates a petition for {} with an initial bid of {}".format(me, card, initialBid))
            me.Bid = initialBid
            setGlobalVariable("petitionedCard", card._id)
   
def searchUniques(card, name, type = 'deploy'): # Checks if there is a unique card on the table with the same name as the one about to be deployed.
    allUniques = (c for c in table # Make a comprehension of all the cards on the table
        if c.Decktype == 'Imperial' # That are from Imperial Deck (only those are unique)
        and c.isFaceUp # This is apparently not taken into account. The game still includes the face down cards if they match the other conditions.
        and c.name == name # That have the same name as the one being deployed.
        and c != card) # And that are not the same card object as the one about to be deployed. 
                       # I don't know why, but the comprehension grabs this card if this isn't here, even though I filtered the comprehension to disregard face down cards.
    for unique in allUniques:
        if type == 'petition': notify("{} wanted to petition for {} but it's already controlled by {}.".format(me, name, unique.controller))   
        else: notify("{} wanted to deploy {} but it's already controlled by {}.".format(me, name, unique.controller)) 
        return 'NOK'
    return 'OK'

def searchNatives(subtype):
    if re.search(r'Native', subtype):
        if DuneFiefs() == 0: 
            if not confirm("You must control at least one Dune Fief in order to deploy a Native Persona. \n\nAre you sure you want to proceed?"): return 'NOK'
    return 'OK'
    
def restoreAll(group, x = 0, y = 0): 
    mute()
    if shared.Phase != 1: #One can only disengage during the Opening Interval
      whisper("You can only disengage all cards during the Opening Interval")
      return
    myCards = (card for card in table
               if card.controller == me
               and card.owner == me)
    for card in myCards:
        card.orientation &= ~Rot90
        if card.markers[Assembly] > 0 and card.isFaceUp:
             card.markers[Assembly] = 0
    notify("{} disengages all his cards.".format(me))

def addSpice(card, x = 0, y = 0):
    mute()
    notify("{} adds a Spice token to {}.".format(me, card))
    card.markers[Spice] += 1

def subSpice(card, x = 0, y = 0):
    mute()
    notify("{} removes a Spice token from {}.".format(me, card))
    card.markers[Spice] -= 1

def addDeferment(card, x = 0, y = 0):
    mute()
    notify("{} adds a Deferment token on {}.".format(me, card))
    card.markers[Deferment_Token] += 1

def subDeferment(card, x = 0, y = 0):
    mute()
    notify("{} removes a Deferment token on {}.".format(me, card))
    card.markers[Deferment_Token] -= 1

def addProgram(card, x = 0, y = 0):
    mute()
    notify("{} adds a Program token to {}.".format(me, card))
    card.markers[Program] += 1
    
def switchAssembly(card, x = 0, y = 0):
   mute()
   if card.markers[Assembly] == 0:
      notify("{} marks {} as an Assembly card.".format(me, card))
      card.markers[Assembly] = 1
      assemblyCards.append(card)
   else:
      notify("{} takes {} out of the Imperial Assembly.".format(me, card))
      card.markers[Assembly] = 0
      assemblyCards.remove(card)

def CHOAMbuy(group, x = 0, y = 0): # This function allows the player to purchase spice through checks and balances to avoid mistakes.
    global CHOAMDone # Import the variable which informs us if the player has done another CHOAM exchange this turn
    mute()
    spiceNR = 0 # Variable we use to remember how much spice they want to buy
    if CHOAMDone == 1: # If the player has already done a CHOAM exchange, remind them, but let them continue if they want, in case they have a card effect allowing them to do so.
       if not confirm("You've already done a CHOAM exchange this round. Are you sure you're allowed to do another?"): return
       else: notify("{} is performing another CHOAM Exchange this round.".format(me)) # However if they proceed, alter the message to point it out.
    if CHOAMDone == 0: notify("{} is performing a CHOAM Exchange.".format(me)) # Inform everyone that the player is beggingin a CHOAM exchange.
    while spiceNR > 3 or spiceNR == 0: # We start a loop, so that if the player can alter their number if they realize they don't have enough.
       spiceNR = askInteger("How much spice do you want to buy (Max 3. {} Solaris for the first spice and there are {} spice left in the Guild Hoard)?\n\nRemember that you can only do one CHOAM Exchange per round!".format(shared.CROE, shared.counters['Guild Hoard'].value), 0)
       if spiceNR == 0 or spiceNR == None: 
          notify("{} has cancelled the CHOAM exchange".format(me))
          return # If the player answered 0 or closed the window, cancel the exchange and inform.
       elif spiceNR > 0 and spiceNR < 4:  # If they are within the right value of 1-3...
          fullcost = completeSpiceCost(spiceNR) # Calculate how much the spice they want to purchase would cost. 
          if spiceNR > shared.counters['Guild Hoard'].value:  # Check if the hoard has enough spice left.
             whisper("The hoard does not have enough spice for you to buy.")
             spiceNR = 0 # We do this so that the player stays in the loop and gets asked again
          elif me.Solaris < fullcost: # Check if the player can pay it.
             whisper("You do not have enough solaris in your treasury to buy {} Spice from the hoard. You need at least {}".format(spiceNR, fullcost))
             spiceNR = 0 # We do this so that the player stays in the loop and gets asked again
          else: 
             me.Solaris -=fullcost # Player pays here.
             me.Spice += spiceNR # Then they get their spice.
             shared.counters['Guild Hoard'].value -= spiceNR # Then the spice is taken away from the hoard.
             shared.CROE = CROEAdjust(shared.counters['Guild Hoard'].value) # Then the CROE is reset.
             notify("{} has bought {} Spice for {}. The Guild Hoard now has {} Spice left and the CROE is set at {}".format(me, spiceNR, fullcost, shared.counters['Guild Hoard'].value, shared.CROE))
             CHOAMDone = 1 # Then mark that the player has done their CHOAM exchange for the turn.
       else:
          whisper("You cannot buy more than 3 spice per CHOAM Exchange.")
        

def CHOAMsell(group, x = 0, y = 0): # Very similar as CHOAMbuy, but player sells spice instead.
    global CHOAMDone
    mute()
    spiceNR = 0
    if CHOAMDone == 1:
       if not confirm("You've already done a CHOAM exchange this round. Are you sure you're allowed to do another?"): return
       else: notify("{} is performing another CHOAM Exchange this round.".format(me))
    if CHOAMDone == 0: notify("{} is performing a CHOAM Exchange.".format(me))
    while spiceNR > 3 or spiceNR == 0:
       spiceNR = askInteger("How much spice do you want to sell (Max 3. {} Solaris for the first spice and there are {} spice currently in the Guild Hoard)?\n\nRemember that you can only do one CHOAM Exchange per round!".format(shared.CROE, shared.counters['Guild Hoard'].value), 0)
       if spiceNR == 0 or spiceNR == None:
          notify("{} has cancelled the CHOAM exchange".format(me))
          return
       elif spiceNR > 0 and spiceNR < 4: 
          if me.Spice - spiceNR < 0: 
             whisper("You do not have this amount of spice to sell. You have only {} to sell.".format(me.Spice))
             spiceNR = 0 # We do this so that the player stays in the loop and gets asked again
          else: 
             fullcost = completeSpiceCost(-spiceNR)
             me.Solaris +=fullcost
             me.Spice -= spiceNR
             shared.counters['Guild Hoard'].value += spiceNR
             shared.CROE = CROEAdjust(shared.counters['Guild Hoard'].value)
             notify("{} has sold {} Spice for {}. The Guild Hoard now has {} Spice left and the CROE is set at {}".format(me, spiceNR, fullcost, shared.counters['Guild Hoard'].value, shared.CROE))
             CHOAMDone = 1
       else:
          whisper("You cannot sell more than 3 spice per CHOAM Exchange.")

def resetBank(group, x=0, y=0): # Asks the player to set the amount of spice there should be in the bank and resets the CROE.
   mute()
   currentbank = shared.counters['Guild Hoard'].value
   newbank = askInteger("Set the bank at how many spice?\n[Currently at {} Spice]\n\n(Hint: close this window to simply reset the CROE for the current number of spice)".format(currentbank), currentbank)
   if newbank == None: newbank = currentbank
   if newbank >= currentbank: difference = '+' + str(newbank - currentbank)
   elif currentbank > newbank: difference = '-' + str(currentbank - newbank)
   shared.CROE = CROEAdjust(newbank)
   shared.counters['Guild Hoard'].value = newbank 
   notify("{} has reset the Guild Hoard to {} Spice ({}). The CROE is now {}".format(me,shared.counters['Guild Hoard'].value, difference, shared.CROE))

def completeSpiceCost(count = 1): # This takes as input how many spice we want to buy or sell, and returns how much it's going to cost in total.
   i = 0
   cost = 0
   simulatedHoard = shared.counters['Guild Hoard'].value #We use simulated numbers in order to avoid touching the counters.
   simulatedCROE = shared.CROE 
   if count > 0:
      while i < count:
         cost += simulatedCROE
         simulatedHoard -= 1
         simulatedCROE = CROEAdjust(simulatedHoard)
         i += 1
      return cost
   elif count < 0:
      while i > count:
         cost += simulatedCROE
         simulatedHoard += 1
         simulatedCROE = CROEAdjust(simulatedHoard)
         i -= 1
      return cost
 

def CROEAdjust(hoard): # We need to pass the guild hoard number here. We cannot set it as default when it's not provided. It bugs out.
   if hoard == 0: return 6
   elif hoard >0 and hoard < 4: return 5
   elif hoard >3 and hoard < 7: return 4
   elif hoard >6 and hoard < 10: return  3
   elif hoard >9 and hoard < 13: return 2
   elif hoard >12: return 1
   else: notify("Why is the Guild Hoard at a {}?".format(hoard)) # Notify the players, in case the counter is set below 0 by mistake.

def buyFavor(group, x = 0, y = 0): # Very similar to CHOAMbuy, but player buys Favour instead, which is simpler.
    global favorBought
    mute()
    favorNR = 0
    if favorBought == 1:
       if not confirm("You've already bought favor this round. Are you sure you're allowed to buy more?"): return
       else: notify("{} is performing another favor purchase this round.".format(me))
    if favorBought == 0: notify("{} is performing a favor purchase.".format(me))
    while favorNR > 5 or favorNR == 0:
       favorNR = askInteger("How much Imperial favor do you want to purchase (Max 5, 2 Solaris per Favor)?\n\n(Remember that you can only purchase favor once per round!)", 0)
       if favorNR == 0 or favorNR == None:
          notify("{} has cancelled the favor purchase".format(me))
          return
       elif favorNR > 0 and favorNR < 6: 
          fullcost = favorNR * 2
          if me.Solaris < fullcost: 
             whisper("You do not have enough solaris in your treasury to buy {} favor. You need at least {}".format(favorNR, fullcost))
             favorNR = 0 # We do this so that the player stays in the loop and gets asked again
          else: 
             me.Solaris -=fullcost
             me.Favor += favorNR
             notify("{} has bought {} favor. They now have {} favor".format(me, favorNR, me.Favor))
             favorBought = 1
       else:
          whisper("You cannot buy more than 5 favor per exchange.")


def automatedOpening(group, x = 0, y = 0):
   global favorBought, CHOAMDone, DeployedDuneEvent, DeployedImperiumEvent, inactiveProgram
   favorBought = 0 # Reset the player's favor exchanges for the round.
   CHOAMDone = 0 # Reset the player's CHOAM exchanges for the round.
   DeployedDuneEvent = 0 # Reset the amount of Dune events for this round.
   DeployedImperiumEvent = 0 # Reset the amount of Imperium events for this round.
   mute()
   if shared.Phase != 1: # This function is allowed only during the Opening Interval
      whisper("You can only perform this action during the Opening Interval")
      return
   myCards = (card for card in table if card.controller == me and card.owner == me)
   for card in myCards:
      if card.highlight != DoesntDisengageColor: card.orientation &= ~Rot90 # If a card can disengage, disengage it.
      if card.markers[Assembly] > 0 and card.isFaceUp: card.markers[Assembly] = 0 # If a card came from the assembly last turn. Remove its special assembly marker.
      if not card.isFaceUp and card.markers[Assembly] == 0: card.markers[Deferment_Token] += 1 # If a card is not an Assembly or Program and is face down (subdued), add a deferment token on it.
      try: # We don't want to put deferment tokens on inactive programs.
         if inactiveProgram[card]: card.markers[Deferment_Token] = 0
      except KeyError: pass   
   notify("{} disengaged all his cards and added deferment tokens to all subdued ones.".format(me))
   setGlobalVariable("petitionedCard", "Empty") # Clear the shared variables, just in case any of them are stuck
   setGlobalVariable("passedPlayers", "[]")

def automatedClosing(group, x = 0, y = 0):
   if shared.Phase != 3: # This function is allowed only during the Closing Interval
      whisper("You can only perform this action during the Closing Interval")
      return
   if me.Favor < 1 and len(me.hand) < handsize:
      notify("{} cannot not refill their hand because they have less than 1 Imperial favor. Is {} is defeated?".format(me, me))
      return   
   if not confirm("Have you remembered to discard any cards you don't want from your hand and Assembly?"): return
   refill()
   myCards = (card for card in table
              if card.controller == me
              and card.owner == me
              and card.Type == 'Event'
              and card.isFaceUp)
   for card in myCards:
      if re.search(r'Nexus', card.Subtype): 
         card.markers[Deferment_Token] -= 1 # Nexus events lose one deferment token per House discard phase.
         if card.markers[Deferment_Token] == 0: # If Nexus events lose their last deferment token, they are discarded.
            card.moveTo(me.piles['House Discard'])
            notify ("{}'s Nexus Event {} has expired and was automatically discarded".format(me, card))
      elif re.search(r'Duration Effect', card.Operation): 
         card.moveTo(me.piles['House Discard']) # Duration events are discarded at the end of the turn.
         notify ("{}'s Duration Effect from {} has expired and was automatically discarded".format(me, card))
   notify("{} refills their hand back to {} and their Imperial Assembly to {}.".format(me, handsize, assemblysize))
   

def doesNotDisengage(card, x = 0, y = 0): # Mark a card as "Does not disengage" or unmark it. We use a card highlight to do this.
   if card.highlight == DoesntDisengageColor: # If it's already marked, remove highlight from it and inform.
      card.highlight = None
      notify("{}'s {} can now Disengage during Opening Interval.".format(me, card))
   else:
      card.highlight = DoesntDisengageColor # Otherwise highlight it and inform. 
      notify("{}'s {} will not Disengage during Opening Interval.".format(me, card))

def discard(cards, x = 0, y = 0): # Discard a card.
   mute()
   for card in cards: # Can be done at more than one card at the same time, since attached cards follow their parent always.
      cardowner = card.owner
      card.isFaceUp = True
      if card in assemblyCards: assemblyCards.remove(card)
      if card.Decktype == 'Imperial': card.moveTo(cardowner.piles['Imperial Discard'])
      else: card.moveTo(cardowner.piles['House Discard'])
      notify("{} has discarded {}.".format(me, card))

def produceSpice(card, x = 0, y = 0):
   mute()
   spiceNR = askInteger("How much spice to produce directly into the Guild Hoard?", 1)
   if spiceNR == 0: return
   card.orientation = Rot90
   shared.counters['Guild Hoard'].value += spiceNR
   shared.CROE = CROEAdjust(shared.counters['Guild Hoard'].value)
   notify("{} has engaged {} to produce {} spice directly into the Guild Hoard. The Guild Hoard now has {} Spice and the CROE is set at {}".format(me, card, spiceNR, shared.counters['Guild Hoard'].value, shared.CROE))

#------------------------------------------------------------------------------
# Hand Actions
#------------------------------------------------------------------------------

def payCost(count = 1, notification = silent): # Automatically pays the cost of a card being played from your hand, or confirms/informs if you can't play it.
   count = num(count)
   if count == 0 : return 'OK'
   if me.Solaris < count:  
      if not confirm("You do not seem to have enough Solaris in your House Treasury to pay the cost. \n\nAre you sure you want to proceed? \
      \n(If you do, your solaris will go to the negative. You will need to increase it manually as required.)"): return 'ABORT'
      if notification == loud: notify("{} was supposed to pay {} Solaris but only has {} in their house treasury. They'll need to reduce the cost by {} with card effects.".format(me, count, me.Solaris, count - me.Solaris))   
      me.Solaris -= count
   else: 
      me.Solaris -= count
      if notification == loud: notify("{} has paid {} Solaris. {} is left their house treasury".format(me, count, me.Solaris))  
   return 'OK'

def play(card, x = 0, y = 0):
   global totalevents
   mute()
   src = card.group
   # The function below checks if the player is allowed to play this house card. House cards can only be played if the player has one card of same allegiance in their Imperial deck.
   if card.Allegiance != 'None' and card.Allegiance != '' and card.Allegiance not in allegiances: 
      if confirm("{}'s Allegiance ({}) does not exist your Imperial Deck. You are not normally allowed have it in your deck. \n\nContinue?".format(card.name, card.Allegiance)):
         notify("{}'s Allegiance does not exist in {}'s Imperial Deck. Illegal deck?".format(card, me))
      else: return
   if card.Type == 'Event':  # Events are placed face down.
      placeCard(card, 'PlayEvent')
      notify("{} plays an event from their hand.".format(me))
      totalevents += 1 # This is used to moves every new event a bit from the old one, to avoid stacking them and making them invisible.
      if totalevents == 11: totalevents = 0
   elif card.Type == 'Persona' and re.search(r'Native', card.Subtype): # A player can only play aides with subtype "Native" if they control a "Dune Fief".
      if DuneFiefs() == 0: 
         if confirm("You must control at least one Dune Fief in order to play a Native aide. \n\nAre you sure you want to proceed?"):
            if payCost(card.properties['Deployment Cost'], loud) == 'OK': # Take cost out of the bank, if there is any.
               placeCard(card, "DeployPersona")
               notify("{} plays {} from their hand.".format(me, card))
      else: 
         if payCost(card.properties['Deployment Cost'], loud) == 'OK': # Take cost out of the bank, if there is any.
            placeCard(card, "DeployPersona")
            notify("{} plays {} from their hand.".format(me, card))
   elif card.Type == 'Persona':
      if payCost(card.properties['Deployment Cost'], loud) == 'OK':# Take cost out of the bank, if there is any.
         placeCard(card, "DeployPersona")
         notify("{} plays {} from their hand.".format(me, card))   
   else:
      if payCost(card.properties['Deployment Cost'], loud) == 'OK':# Take cost out of the bank, if there is any.
         card.moveToTable(0, 0 - yaxisMove(card))
         notify("{} plays {} from their hand.".format(me, card))

def setup(group):
# This function is usually the first one the player does. It will setup their homeworld on their side of the table. 
# It will also shuffle their decks, setup their Assembly and Dune and draw 7 cards for them.
   if shared.Phase == 0: # First check if we're on the pre-setup game phase. 
                     # As this function will play your whole hand and wipe your counters, we don't want any accidents.
#      if not confirm("Have bought all the favour and spice you'll need with your bonus solaris? \n\n(Remember you need 1 solaris per program you're going to install.)"): return
      global PLS, allegiances, inactiveProgram # Import some necessary variables we're using around the game.
      DuneinHand = 0
      mute()
      chooseSide() # The classic place where the players choose their side.
      me.piles['Imperial Deck'].shuffle() # First let's shuffle our decks now that we have the chance.
      me.piles['House Deck'].shuffle()
      for card in group: # For every card in the player's hand... (which should be just their homeworld and possibly some plans)
         if re.search(r'Homeworld', card.Subtype) and card.Type == 'Holding':  # If it's the homeworld...
            placeCard(card,'SetupHomeworld')
            allegiances[0] = card.Allegiance # We make a note of the Allegiance the player is playing this time (used later for automatically losing favour)
         if re.search(r'Program', card.Subtype) and card.Type == 'Plan':  # If it's a program...
            if payCost(1) == 'OK': # Pay the cost of the program
               placeCard(card,'SetupProgram')
               inactiveProgram[card] = True
         if card.model == '2037f0a1-773d-42a9-a498-d0cf54e7a001': # If the player has put Dune in their hand as well...
            placeCard(card,'SetupDune')
            DuneinHand = 1 # Note down that player brought their own Dune, so that we don't generate a second one.
      if DuneinHand == 0: # If the player didn't bring their own Dune, generate a new one on their side.
         Dune = table.create("2037f0a1-773d-42a9-a498-d0cf54e7a001", 0, 0, 1, True) # Create a Dune card in the middle of the table.
         placeCard(Dune,'SetupDune')
      noteAllegiances() # Note down the rest allegiances of the player
      shared.counters['Guild Hoard'].value = 4 + len(players) * 2 # Starting Spice is 4 + (Nr of players * 2)
      shared.CROE = CROEAdjust(shared.counters['Guild Hoard'].value)
      startFav = -1
      startSpice = -1
      while startSpice < 0 or startSpice >= 5: # keep asking the amount until a valid number is given.
         startSpice = askInteger("How much spice do you want to buy with your bonus solaris?\n\n({} per Spice)".format(shared.CROE + 1), 0)
         if payCost(startSpice * (shared.CROE + 1)) == 'ABORT': startSpice = -1
      me.Spice += startSpice
      while startFav < 0 or startFav >= 5: 
         startFav = askInteger("How much favor do you want to buy with your bonus solaris?\n\n(2 per favor)", 0)
         if payCost(startFav * 2) == 'ABORT': startFav = -1         
      me.Favor += startFav
      me.Solaris += 20     
      refill() # We fill the player's play hand to their hand size (usually 5)
      notify("{} is playing {}. Their starting Solaris is {} and their Imperial Favour is {}. They have {} Programs".format(me, allegiances[0], me.Solaris, me.Favor, totalprogs))  
   else: whisper('You can only setup your starting cards during the Pre-Game setup phase') # If this function was called outside the pre-game setup phase
            
def setHandSize(group): # A function to modify a player's hand size. This is used during Closing Interval when refilling the player's hand automatically.
   global handsize
   tempsize = askInteger("What is your current hand size?", handsize)
   if tempsize == None: return
   else: handsize = tempsize
   notify("{} sets their hand size to {}".format(me, handsize))

def setAssemblySize(group): # A function to modify a player's hand size. This is used during Closing Interval when refilling the player's hand automatically.
   global assemblysize
   tempsize = askInteger("What is your current Assembly limit?", assemblysize)
   if tempsize == None: return
   else: assemblysize = tempsize
   notify("{} sets their Assembly limit to {}".format(me, assemblysize))
   
def refill(group = me.hand): # Refill the player's hand to its hand size.
   if len(me.hand) < handsize: drawMany(me.piles['House Deck'], handsize - len(me.hand), silent) # If there's less cards than the handsize, draw from the deck until it's full.
   if len(assemblyCards) < assemblysize: imperialDraw(times = assemblysize - len(assemblyCards))

def handDiscard(card, x = 0, y = 0): # Discard a card from your hand.
   mute()
   card.moveTo(me.piles['House Discard'])
   notify("{} has discarded {}.".format(me, card))  

def randomDiscard(group): # Discard a card from your hand randomly.
   mute()
   card = group.random() # Select a random card
   if card == None: return # If hand is empty, do nothing.
   notify("{} randomly discards a card.".format(me)) # Inform that a random card was discarded
   card.moveTo(me.piles['House Discard']) # Move the card in the discard pile.

#------------------------------------------------------------------------------
# Pile Actions
#------------------------------------------------------------------------------

def draw(group):
    if len(group) == 0: return
    i = 0
    mute()
    group.top().moveTo(me.hand)
    notify("{} draws a card.".format(me))

def imperialDraw(group = me.piles['Imperial Deck'], times = 1):
   if len(group) == 0: return
   mute()
   for i in range(times):
      card = group.top()
      card.moveToTable(0,0, True)
      card.markers[Assembly] = 1
      assemblyCards.append(card)
   for n in range(len(assemblyCards)): # Reorganizing the assembly cards.
      card = assemblyCards[n]
      if playeraxis == Yaxis:
         card.moveToTable(PLS * cwidth(card) + PLS * (len(assemblyCards) - 2) * (cwidth(card) / 2) - PLS * n * cwidth(card), homeDistance(card) + cardDistance(card) - yaxisMove(card,'force'),True)
      else: 
         card.moveToTable(homeDistance(card) + cardDistance(card), PLS * cheight(card)  + PLS * (len(assemblyCards) - 2) * (cheight(card) / 2) - n * PLS * cheight(card),True)
    
def shuffle(group):
  group.shuffle()

def drawMany(group, count = None, notification = loud): # This function draws a variable number cards into the player's hand.
    mute()
    if count == None: count = askInteger("Draw how many cards?", 7)
    if len(group) < count: 
       notify("{}'s House deck has {} cards and they attempted to draw {} cards. Did they just lose the game?.".format(me, len(group), count))
       return
    for c in group.top(count): c.moveTo(me.hand)
    if notification == loud : notify("{} draws {} cards to their play hand.".format(me, count)) # And if we're "loud", notify what happened.

def mill(group):
   mute()
   if len(group) == 0: return
   count = askInteger("Discard how many cards?", 3)
   for c in group.top(count): c.moveTo(me.piles['House Discard'])
   notify("{} discards the top {} cards from their house deck.".format(me, count))