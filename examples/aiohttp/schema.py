import random
import asyncio
import graphene

from graphql_ws.pubsub import AsyncioPubsub

pubsub = AsyncioPubsub()


class Query(graphene.ObjectType):
    base = graphene.String()

    async def resolve_base(root, info):
        return 'Hello World!'


class MutationExample(graphene.Mutation):
    class Arguments:
        input_text = graphene.String()

    output_text = graphene.String()

    async def mutate(self, info, input_text):
        await pubsub.publish('BASE', input_text)
        return MutationExample(output_text=input_text)


class Mutations(graphene.ObjectType):
    mutation_example = MutationExample.Field()


class RandomType(graphene.ObjectType):
    seconds = graphene.Int()
    random_int = graphene.Int()


class Subscription(graphene.ObjectType):
    count_seconds = graphene.Float(up_to=graphene.Int())
    random_int = graphene.Field(RandomType)
    mutation_example = graphene.String()

    async def resolve_mutation_example(root, info):
        try:
            sub_id, q = pubsub.subscribe_to_channel('BASE')
            while True:
                payload = await q.get()
                yield payload
        finally:
            pubsub.unsubscribe('BASE', sub_id)

    async def resolve_count_seconds(root, info, up_to=5):
        for i in range(up_to):
            print("YIELD SECOND", i)
            yield i
            await asyncio.sleep(1.)
        yield up_to

    async def resolve_random_int(root, info):
        i = 0
        while True:
            yield RandomType(seconds=i, random_int=random.randint(0, 500))
            await asyncio.sleep(1.)
            i += 1


schema = graphene.Schema(query=Query, mutation=Mutations,
                         subscription=Subscription)
