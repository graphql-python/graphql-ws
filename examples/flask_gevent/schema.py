import random
import graphene
from rx import Observable


class Query(graphene.ObjectType):
    base = graphene.String()


class RandomType(graphene.ObjectType):
    seconds = graphene.Int()
    random_int = graphene.Int()


class Subscription(graphene.ObjectType):

    count_seconds = graphene.Int(up_to=graphene.Int())

    random_int = graphene.Field(RandomType)

    def resolve_count_seconds(root, info, up_to=5):
        return (
            Observable.interval(1000)
            .map(lambda i: "{0}".format(i))
            .take_while(lambda i: int(i) <= up_to)
        )

    def resolve_random_int(root, info):
        return Observable.interval(1000).map(
            lambda i: RandomType(seconds=i, random_int=random.randint(0, 500))
        )


schema = graphene.Schema(query=Query, subscription=Subscription)
