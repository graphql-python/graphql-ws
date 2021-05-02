GRAPHQL_WS = "graphql-ws"
WS_PROTOCOL = GRAPHQL_WS
TRANSPORT_WS_PROTOCOL = "graphql-transport-ws"

GQL_CONNECTION_INIT = "connection_init"  # Client -> Server
GQL_CONNECTION_ACK = "connection_ack"  # Server -> Client
GQL_CONNECTION_ERROR = "connection_error"  # Server -> Client

# NOTE: This one here don't follow the standard due to connection optimization
GQL_CONNECTION_TERMINATE = "connection_terminate"  # Client -> Server
GQL_CONNECTION_KEEP_ALIVE = "ka"  # Server -> Client
GQL_START = "start"  # Client -> Server  (graphql-ws)
GQL_SUBSCRIBE = "subscribe"  # Client -> Server  (graphql-transport-ws START equivalent)
GQL_DATA = "data"  # Server -> Client  (graphql-ws)
GQL_NEXT = "next"  # Server -> Client  (graphql-transport-ws DATA equivalent)
GQL_ERROR = "error"  # Server -> Client
GQL_COMPLETE = "complete"  # Server -> Client
# (and Client -> Server for graphql-transport-ws STOP equivalent)
GQL_STOP = "stop"  # Client -> Server  (graphql-ws only)
