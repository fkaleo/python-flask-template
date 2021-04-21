from index import Event, Context


def handle(event: Event, context: Context):
    # TODO implement
    return {
        "statusCode": 200,
        "body": "Hello from OpenFaaS!"
    }