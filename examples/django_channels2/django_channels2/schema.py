import asyncio

import graphene
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

channel_layer = get_channel_layer()


class Query(graphene.ObjectType):
    hello = graphene.String()

    def resolve_hello(self, info, **kwargs):
        return "world"


class TestMessageMutation(graphene.Mutation):
    class Arguments:
        input_text = graphene.String()

    output_text = graphene.String()

    def mutate(self, info, input_text):
        async_to_sync(channel_layer.group_send)("new_message", {"data": input_text})
        return TestMessageMutation(output_text=input_text)


class Mutations(graphene.ObjectType):
    test_message = TestMessageMutation.Field()


class Subscription(graphene.ObjectType):
    count_seconds = graphene.Int(up_to=graphene.Int())
    new_message = graphene.String()

    async def resolve_count_seconds(self, info, up_to=5):
        i = 1
        while i <= up_to:
            yield str(i)
            await asyncio.sleep(1)
            i += 1

    async def resolve_new_message(self, info):
        channel_name = await channel_layer.new_channel()
        await channel_layer.group_add("new_message", channel_name)
        try:
            while True:
                message = await channel_layer.receive(channel_name)
                yield message["data"]
        finally:
            await channel_layer.group_discard("new_message", channel_name)


schema = graphene.Schema(query=Query, mutation=Mutations, subscription=Subscription)
