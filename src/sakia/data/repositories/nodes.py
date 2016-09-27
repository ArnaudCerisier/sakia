import attr
import json

from ..entities import Node


@attr.s(frozen=True)
class NodesRepo:
    """The repository for Communities entities.
    """
    _conn = attr.ib()  # :type sqlite3.Connection
    _primary_keys = (Node.currency, Node.pubkey)

    def insert(self, node):
        """
        Commit a node to the database
        :param sakia.data.entities.Node node: the node to commit
        """
        with self._conn:
            node_tuple = attr.astuple(node, tuple_factory=list)
            node_tuple[2] = '\n'.join([e.inline() for e in node_tuple[2]])
            node_tuple[8] = json.dumps(node_tuple[8])
            values = ",".join(['?'] * len(node_tuple))
            self._conn.execute("INSERT INTO nodes VALUES ({0})".format(values), node_tuple)

    def update(self, node):
        """
        Update an existing node in the database
        :param sakia.data.entities.Node node: the node to update
        """
        with self._conn:
            updated_fields = attr.astuple(node, tuple_factory=list,
                                          filter=attr.filters.exclude(*NodesRepo._primary_keys))
            updated_fields[0] = '\n'.join([e.inline() for e in updated_fields[0]])
            updated_fields[6] = json.dumps(updated_fields[6])
            where_fields = attr.astuple(node, tuple_factory=list,
                                        filter=attr.filters.include(*NodesRepo._primary_keys))
            self._conn.execute("""UPDATE nodes SET
                                        endpoints=?,
                                        current_buid=?,
                                        previous_buid=?,
                                        state=?,
                                        software=?,
                                        version=?,
                                        merkle_nodes=?
                                       WHERE
                                       currency=? AND
                                       pubkey=?""",
                                       updated_fields + where_fields)

    def get_one(self, **search):
        """
        Get an existing node in the database
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Node
        """
        with self._conn:
            filters = []
            values = []
            for k, v in search.items():
                filters.append("{k}=?".format(k=k))
                values.append(v)

            request = "SELECT * FROM nodes WHERE {filters}".format(filters=" AND ".join(filters))

            c = self._conn.execute(request, tuple(values))
            data = c.fetchone()
            if data:
                return Node(*data)

    def get_all(self, **search):
        """
        Get all existing node in the database corresponding to the search
        :param dict search: the criterions of the lookup
        :rtype: sakia.data.entities.Node
        """
        with self._conn:
            filters = []
            values = []
            for k, v in search.items():
                value = v
                filters.append("{key} = ?".format(key=k))
                values.append(value)

            request = "SELECT * FROM nodes WHERE {filters}".format(filters=" AND ".join(filters))

            c = self._conn.execute(request, tuple(values))
            datas = c.fetchall()
            if datas:
                return [Node(*data) for data in datas]
        return []

    def drop(self, node):
        """
        Drop an existing node from the database
        :param sakia.data.entities.Node node: the node to update
        """
        with self._conn:
            where_fields = attr.astuple(node, filter=attr.filters.include(*NodesRepo._primary_keys))
            self._conn.execute("""DELETE FROM nodes
                                  WHERE
                                  currency=? AND pubkey=?""", where_fields)