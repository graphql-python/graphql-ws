import graphene
import random

from graphql_ws.pubsub import GeventRxPubsub
from rx import Observable

pubsub = GeventRxPubsub()


class Query(graphene.ObjectType):
    base = graphene.String()

    def resolve_base(root, info):
        return 'Hello World!'


class MutationExample(graphene.Mutation):
    class Arguments:
        input_text = graphene.String()

    output_text = graphene.String()

    def mutate(self, info, input_text):
        pubsub.publish('BASE', input_text)
        return MutationExample(output_text=input_text)


class Mutations(graphene.ObjectType):
    mutation_example = MutationExample.Field()


class RandomType(graphene.ObjectType):
    seconds = graphene.Int()
    random_int = graphene.Int()


class Subscription(graphene.ObjectType):
    count_seconds = graphene.Int(up_to=graphene.Int())
    random_int = graphene.Field(RandomType)
    mutation_example = graphene.String()

    def resolve_mutation_example(root, info):
        # subscribe_to_channel method returns an observable
        return pubsub.subscribe_to_channel('BASE')\
                         .map(lambda i: "{0}".format(i))

    def resolve_count_seconds(root, info, up_to=5):
        return Observable.interval(1000)\
                         .map(lambda i: "{0}".format(i))\
                         .take_while(lambda i: int(i) <= up_to)

    def resolve_random_int(root, info):
        return Observable.interval(1000).map(
            lambda i: RandomType(seconds=i, random_int=random.randint(0, 500)))


schema = graphene.Schema(query=Query, mutation=Mutations,
                         subscription=Subscription)
