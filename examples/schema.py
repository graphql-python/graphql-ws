from collections import OrderedDict
from asyncio import sleep
import graphene


class Query(graphene.ObjectType):
    base = graphene.String()


class Subscription(graphene.ObjectType):
    count_seconds = graphene.Float(up_to=graphene.Int())

    async def resolve_count_seconds(root, info, up_to):
        for i in range(up_to):
            print("YIELD SECOND", i)
            yield i
            await sleep(1.)
        yield up_to


schema = graphene.Schema(query=Query, subscription=Subscription)
