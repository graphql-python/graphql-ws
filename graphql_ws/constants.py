GRAPHQL_WS = 'graphql-ws'
WS_PROTOCOL = GRAPHQL_WS

GQL_CONNECTION_INIT = 'connection_init'  # Client -> Server
GQL_CONNECTION_ACK = 'connection_ack'  # Server -> Client
GQL_CONNECTION_ERROR = 'connection_error'  # Server -> Client

# NOTE: This one here don't follow the standard due to connection optimization
GQL_CONNECTION_TERMINATE = 'connection_terminate'  # Client -> Server
GQL_CONNECTION_KEEP_ALIVE = 'ka'  # Server -> Client
GQL_START = 'start'  # Client -> Server
GQL_DATA = 'data'  # Server -> Client
GQL_ERROR = 'error'  # Server -> Client
GQL_COMPLETE = 'complete'  # Server -> Client
GQL_STOP = 'stop'  # Client -> Server
