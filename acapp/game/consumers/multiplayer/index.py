from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.conf import settings
from django.core.cache import cache

class MultiPlayer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()                  ## 创立连接函数

    async def disconnect(self, close_code):
        print('disconnect')
        await self.channel_layer.group_discard(self.room_name, self.channel_name);  ## 可以将不同的连接加到一个组里


    async def create_player(self, data):
        self.room_name = None

        start = 0

        for i in range(start, 100000000):      ### 寻找房间 
            name = "room-%d" % (i)
            if not cache.has_key(name) or len(cache.get(name)) < settings.ROOM_CAPACITY:    ### 没有房间或者找到人数小于3的房间 
                self.room_name = name                 ### 获取房间号
                break

        if not self.room_name:               ### 如果房间爆满则退出
            return

        if not cache.has_key(self.room_name):        ### 如果没有房间则创建一个房间
            cache.set(self.room_name, [], 3600)  # 有效期1小时

        for player in cache.get(self.room_name):    ### 创建完房间后，遍历一下房间内的已有玩家，把其他玩家信息发送回给当前玩家，并返回给当前玩家的前端
            await self.send(text_data=json.dumps({  ### json.dumps(字典) #将字典转化成字符串
                'event': "create_player",
                'uuid': player['uuid'],
                'username': player['username'],
                'photo': player['photo'],
            }))

        await self.channel_layer.group_add(self.room_name, self.channel_name)  

        players = cache.get(self.room_name)   ### 将我的信息加入的组内
        players.append({
            'uuid': data['uuid'],
            'username': data['username'],
            'photo': data['photo']
        })
        cache.set(self.room_name, players, 3600)  # 有效期1小时
        await self.channel_layer.group_send(   ### 群发信息函数，再把我的信息广播给组内的。
            self.room_name,
            {
                'type': "group_send_event",
                'event': "create_player",
                'uuid': data['uuid'],
                'username': data['username'],
                'photo': data['photo'],
            }
        )

    async def group_send_event(self, data):     ### 用来接收上面群发信息的函数，把组内的信息打包发给前端
        await self.send(text_data=json.dumps(data)) 

    async def move_to(self, data):
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': "group_send_event",
                'event': "move_to",
                'uuid': data['uuid'],
                'tx': data['tx'],
                'ty': data['ty'],
            }
        )

    async def shoot_fireball(self, data):
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': "group_send_event",
                'event': "shoot_fireball",
                'uuid': data['uuid'],
                'tx': data['tx'],
                'ty': data['ty'],
                'ball_uuid': data['ball_uuid'],
            }
        )

    async def attack(self, data):
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': "group_send_event",
                'event': "attack",
                'uuid': data['uuid'],
                'attackee_uuid': data['attackee_uuid'],
                'x': data['x'],
                'y': data['y'],
                'angle': data['angle'],
                'damage': data['damage'],
                'ball_uuid': data['ball_uuid'],
            }
        )

    async def blink(self, data):
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': "group_send_event",
                'event': "blink",
                'uuid': data['uuid'],
                'tx': data['tx'],
                'ty': data['ty'],
            }
        )

    async def message(self, data):
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': "group_send_event",
                'event': "message",
                'uuid': data['uuid'],
                'username': data['username'],
                'text': data['text'],
            }
        )

    async def receive(self, text_data):                 ## 接受前端向后端发送的请求
        data = json.loads(text_data)
        event = data['event']
        if event == "create_player":
            await self.create_player(data)
        elif event == "move_to":
            await self.move_to(data)
        elif event == "shoot_fireball":
            await self.shoot_fireball(data)
        elif event == "attack":
            await self.attack(data)
        elif event == "blink":
            await self.blink(data)
        elif event == "message":
            await self.message(data)


