from random import randrange
import pika
import math

#########################____RPC____START_____##################################





#########################____RPC____END_____####################################

global _game_counter
_game_counter = 0

class Server:
    def __init__(self, name = "Default"):
        self.server_name = name
        self.game_list = []
        self.player_nicknames_list = []

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))

        self.channel = self.connection.channel()

        self.channel.queue_declare(queue='rpc_queue')


    def on_request(self, ch, method, props, body):
        request = body
        id, message = request.split('_')

#####################################################################################################

        if id == '00':
            player_name = message
            if player_name in server.player_nicknames_list:
                ch.basic_publish(exchange='',
                                 routing_key=props.reply_to,
                                 properties=pika.BasicProperties(correlation_id= \
                                                                     props.correlation_id),
                                 body='Wrong NAME')
            else:
                server.player_nicknames_list.append(player_name)
                self.channel.queue_declare(queue=player_name)
                ch.basic_publish(exchange='',
                                routing_key=player_name,
                                body='connected')
                ch.basic_publish(exchange='',
                                 routing_key=props.reply_to,
                                 properties=pika.BasicProperties(correlation_id= \
                                                                     props.correlation_id),
                                 body='OK')
            ch.basic_ack(delivery_tag=method.delivery_tag)

#####################################################################################################

        if id == '01':
            response = server.getGamesList()
            print response
            ch.basic_publish(exchange='',
                             routing_key=props.reply_to,
                             properties=pika.BasicProperties(correlation_id= \
                                                                 props.correlation_id),
                             body=str(response))
            ch.basic_ack(delivery_tag=method.delivery_tag)

#####################################################################################################

        if id == '02':
            field, message = message.split(',')
            number_of_players, playerName = message.split('.')
            game = Game(int(field),int(number_of_players))
            self.game_list.append(game)
            game.addPlayer(Player(playerName,game.size))
            response = 'OK!'  # call of the function that is needed
            #self.channel.queue_declare(queue=playerName)
            ch.basic_publish(exchange='',
                             routing_key=playerName,
                             body='joined')
            ch.basic_publish(exchange='',
                             routing_key=props.reply_to,
                             properties=pika.BasicProperties(correlation_id= \
                                                                 props.correlation_id),
                             body=str(response))
            ch.basic_ack(delivery_tag=method.delivery_tag)


#####################################################################################################

        if id == '03':
            Pname, Gnumber = message.split(',')
            game = server.game_list[int(Gnumber)-1]
            game.addPlayer(Player(Pname,game.size))
            response = str(game.size)
            #self.channel.queue_declare(queue=Pname)
            ch.basic_publish(exchange='',
                             routing_key=Pname,
                             body='joined')
            ch.basic_publish(exchange='',
                             routing_key=props.reply_to,
                             properties=pika.BasicProperties(correlation_id= \
                                                                 props.correlation_id),
                             body=str(response))
            ch.basic_ack(delivery_tag=method.delivery_tag)

######################################################################################################

        if id == '04':
            Pname, BattleF = message.split(',')
            for game in server.game_list:
                for player in game.player_list:
                    if player.nickname == Pname:
                        curr_game = game
            for player in curr_game.player_list:
                if player.nickname == Pname:
                    player.battlefield = player.StringToBattelfield(BattleF)
                    curr_game.counter += 1
            response = 'OK!'
            #self.channel.queue_declare(queue=Pname)
            ch.basic_publish(exchange='',
                             routing_key=Pname,
                             body='wait for game start')
            ch.basic_publish(exchange='',
                             routing_key=props.reply_to,
                             properties=pika.BasicProperties(correlation_id= \
                                                                 props.correlation_id),
                             body=str(response))
            ch.basic_ack(delivery_tag=method.delivery_tag)


####################################################################################################

        if id == '05':
             response = 'OK!'
             for game in server.game_list:
                 for player in game.player_list:
                     if player.nickname == message:
                         curr_game = game
             print curr_game.counter
             if curr_game.counter == curr_game.numPlayers:
                 if curr_game.player_list[0].nickname == message:
                     # self.channel.queue_declare(queue=curr_game.player_list[numb].nickname)
                     ch.basic_publish(exchange='',
                                      routing_key=message,
                                      body='your turn')
                 else:
                     ch.basic_publish(exchange='',
                                      routing_key=message,
                                      body='not your turn')
             ch.basic_publish(exchange='',
                              routing_key=props.reply_to,
                              properties=pika.BasicProperties(correlation_id= \
                                                                  props.correlation_id),
                              body=str(response))
             ch.basic_ack(delivery_tag=method.delivery_tag)




                     ##################################################################################################
    def checkHit(self, x, y, curr_player_name, game_number):
        hit = False
        message = ''
        game = server.game_list[game_number - 1]
        for player in game.player_list:
            if player.nickname != curr_player_name:
                if player.battlefield[x][y] == '1':
                    player.battlefield[x][y] = '2'
                    hit = True
                    game.dict_of_hits[player.nickname].append((x,y))
                    message += player.nickname + ','
        return hit, message


    def getServerName(self):
        return self.server_name

    def getGamesList(self):
        str = ""
        counter = 1
        for game in self.game_list:
            str += "%d. "%counter + game.game_name + "\n"
            counter += 1
        return str

    #Creation of instances of other classes
    def createGame(self, field_size):
        game = Game(field_size)
        self.game_list.append(game)

    def addGame(self, game):
        self.game_list.append(game)

    def createShip(self, ship_size, list_coord):
        return Ship(ship_size, list_coord)

    def createFleet(self, field_size):
        return Fleet(field_size)

    def createPlayer(self, nickname, fleet, field_size):
        return Player(nickname, fleet, field_size)


class Game:
    def __init__(self, field_size, numOfPlayers, name = ""):
        #size of field initialization
        self.size = field_size
        self.numPlayers = numOfPlayers
        self.counter = 0
        #name initialization
        if name:
            self.game_name = name
        else:
            global _game_counter
            self.game_name = "game#%d" % _game_counter
            _game_counter += 1
        #list of players initialization
        self.player_list = []
        self.dict_of_hits = {}

    def addPlayer(self, player):
        self.player_list.append(player)
        self.dict_of_hits[player.nickname] = []

    def getPlayerNicknames(self):
        list_nicknames = []
        for player in self.player_list:
            list_nicknames.append(player.getNickname())
        return list_nicknames

class Player:
    def __init__(self, nickname, game_field_size):
        self.nickname = nickname
        self.battlefield = self.createBattlefield(game_field_size)

    def StringToBattelfield(self,stringBattle):
        battlefield = []
        i = 0
        while i < len(stringBattle):
            x = []
            for j in range(len(self.battlefield)):
                x.append(stringBattle[i + j])
            i += len(self.battlefield)
            battlefield.append(x)
        return battlefield

    def getNickname(self):
        return self.nickname

    def returnBattlefield(self):
        main_str = "    "
        for num in range(len(self.battlefield)):
            if num < 10:
                main_str += (" %s  ") % (num + 1)
            else:
                main_str += ("%s  ") % (num + 1)

        main_str += "\n"
        counter = 1
        for row in self.battlefield:
            if counter < 10:
                str = "%s. |" % counter
            else:
                str = "%s.|" % counter
            for elem in row:
                if elem == 0:
                    str_el = " "
                elif elem == 1:
                    str_el = "#"
                elif elem == 2:
                    str_el = "$"
                elif elem == 3:
                    str_el = "*"
                str += " %s |" % str_el
            counter += 1
            main_str += str
            main_str += "\n"
            main_str += "____"*(len(self.battlefield)+1)
            main_str += "\n"
        return main_str

    def createBattlefield(self, game_field_size):
        battlefield = []
        for i in range(game_field_size):
            battlefield.append([])
            for j in range(game_field_size):
                battlefield[i].append(0)
        return battlefield



    def addPlayersFleetOnBoard(self, fleet):
        self.fleet = fleet
        for ship_list_by_type in [fleet.patrol_boat_list, fleet.destroyer_list, fleet.submarine_list, fleet.carrier_list]:
            for ship in ship_list_by_type:
                if ship:
                    for coordinates in ship.list_coordinates:
                        self.battlefield[coordinates[0]][coordinates[1]] = 1

    #def generateRandomFleet(self, game_field_size):
    #    fleet = Fleet(game_field_size)
    #    temp_battlefield = self.createBattlefield(game_field_size)
    #    for ship_size in [4,3,3,2,2,2,1,1,1,1]:
    #        direction = randrange(2)



class Fleet:
    def __init__(self, game_field_size):
        #!!!!!!!!!!! wrong, change with formula!!!
        self.size = game_field_size
        self.patrol_boat_list = []
        self.destroyer_list = []
        self.submarine_list = []
        self.carrier_list = []
        for i in range(int(math.floor(0.4*self.size))):
            self.patrol_boat_list.append(None)
        for i in range(int(math.floor(0.3 * self.size))):
            self.destroyer_list.append(None)
        for i in range(int(math.floor(0.2 * self.size))):
            self.submarine_list.append(None)
        for i in range(int(math.floor(0.1 * self.size))):
            self.carrier_list.append(None)
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    def addShip(self, ship):
        pb, d, s, c = self.checkFullfil()
        if ship.size == 1:
            self.patrol_boat_list[pb - 1] = ship
        elif ship.size == 2:
            self.destroyer_list[d - 1] = ship
        elif ship.size == 3:
            self.submarine_list[s - 1] = ship
        elif ship.size == 4:
            self.carrier_list[c - 1] = ship

    def checkFullfil(self):
        pb = 0
        d = 0
        s = 0
        c = 0
        for elem in self.patrol_boat_list:
            if not elem:
                pb +=1
        for elem in self.destroyer_list:
            if not elem:
                d += 1
        for elem in self.submarine_list:
            if not elem:
                s += 1
        for elem in self.carrier_list:
            if not elem:
                c += 1
        return pb, d, s, c

    def getNumberOfShips(self, type = "All"):
        if type == "All":
            return len(self.patrol_boat_list) + len(self.destroyer_list) + len(self.submarine_list) + len(self.carrier_list)
        elif type == "PatrolBoat":
            return len(self.patrol_boat_list)
        elif type == "Destroyer":
            return len(self.destroyer_list)
        elif type == "Submarine":
            return len(self.submarine_list)
        elif type == "Carrier":
            return len(self.carrier_list)
        else:
            raise NameError("There is no such type")




class Ship:
    def __init__(self, ship_size, list_coord):
        self.size = ship_size
        if self.size == 1:
            self.name = "PatrolBoat"
        elif self.size == 2:
            self.name = "Destroyer"
        elif self.size == 3:
            self.name = "Submarine"
        elif self.size == 4:
            self.name = "Carrier"
        else:
            raise NameError("Ship size is out of bounds")

        if len(list_coord) == ship_size:
            self.list_coordinates = list_coord
        else:
            raise NameError("The number of coordinates does not correspond to size of a ship")



if __name__ == "__main__":

#########################____RPC____START_____#################################
    server = Server()
    while True:
        try:
            server.channel.basic_qos(prefetch_count=1)
            server.channel.basic_consume(server.on_request, queue='rpc_queue')
            print " [x] Awaiting RPC requests"
            server.channel.start_consuming()
        except:
            pass

#########################____RPC____END_____####################################




