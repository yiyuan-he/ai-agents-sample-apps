# Copyright The OpenTelemetry Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Cassandra instrumentation supporting `cassandra-driver`_ and `scylla-driver`_, it can be enabled by
using ``CassandraInstrumentor``.

.. _cassandra-driver: https://pypi.org/project/cassandra-driver/
.. _scylla-driver: https://pypi.org/project/scylla-driver/

Usage
-----

.. code:: python

    import cassandra.cluster
    from opentelemetry.instrumentation.cassandra import CassandraInstrumentor

    CassandraInstrumentor().instrument()

    cluster = cassandra.cluster.Cluster()
    session = cluster.connect()
    rows = session.execute("SELECT * FROM test")

API
---
"""

from typing import Collection

import cassandra.cluster
from wrapt import wrap_function_wrapper

from opentelemetry import trace
from opentelemetry.instrumentation.cassandra.package import _instruments
from opentelemetry.instrumentation.cassandra.version import __version__
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.utils import unwrap
from opentelemetry.semconv.trace import SpanAttributes


def _instrument(tracer_provider, include_db_statement=False):
    """Instruments the cassandra-driver/scylla-driver module

    Wraps cassandra.cluster.Session.execute_async().
    """
    tracer = trace.get_tracer(
        __name__,
        __version__,
        tracer_provider,
        schema_url="https://opentelemetry.io/schemas/1.11.0",
    )
    name = "Cassandra"

    def _traced_execute_async(func, instance, args, kwargs):
        with tracer.start_as_current_span(
            name, kind=trace.SpanKind.CLIENT
        ) as span:
            if span.is_recording():
                span.set_attribute(SpanAttributes.DB_NAME, instance.keyspace)
                span.set_attribute(SpanAttributes.DB_SYSTEM, "cassandra")
                span.set_attribute(
                    SpanAttributes.NET_PEER_NAME,
                    instance.cluster.contact_points,
                )

                if include_db_statement:
                    query = args[0]
                    span.set_attribute(SpanAttributes.DB_STATEMENT, str(query))

            response = func(*args, **kwargs)
            return response

    wrap_function_wrapper(
        "cassandra.cluster", "Session.execute_async", _traced_execute_async
    )


class CassandraInstrumentor(BaseInstrumentor):
    def instrumentation_dependencies(self) -> Collection[str]:
        return _instruments

    def _instrument(self, **kwargs):
        _instrument(
            tracer_provider=kwargs.get("tracer_provider"),
            include_db_statement=kwargs.get("include_db_statement"),
        )

    def _uninstrument(self, **kwargs):
        unwrap(cassandra.cluster.Session, "execute_async")
