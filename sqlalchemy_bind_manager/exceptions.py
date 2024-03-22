#  Copyright (c) 2024 Federico Busetti <729029+febus982@users.noreply.github.com>
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.


class NotInitializedBindError(Exception):
    """
    Raised when a bind object does not exist (i.e. not yet initialized)
    """

    pass


class UnsupportedBindError(Exception):
    """
    Raised when the internal session handler is given an unsupported bind object.
    Usually it happens when Async and Sync implementation are mixed up
    (i.e. initializing an `AsyncUnitOfWork` instance with a Sync bind)
    """

    pass


class InvalidConfigError(Exception):
    """
    Raised when a class is initialized with an invalid configuration and/or parameters.
    """

    pass


class ModelNotFoundError(Exception):
    """
    Raised when a Repository is not able to find a model using the provided primary key.
    """

    pass


class InvalidModelError(Exception):
    """
    Raised when an invalid model is passed to a Repository object or class.

    i.e.:

     * Trying to instantiate a repository with a non SQLAlchemy model
     * Trying to save a model belonging to another Repository class
    """

    pass


class UnmappedPropertyError(Exception):
    """
    Raised when trying to execute queries using not mapped column names.
    (i.e. passing a non-existing column to `search_params`
    or `order_by` parameters when invoking `find()`)
    """

    pass


class RepositoryNotFoundError(Exception):
    """
    Raised when trying to use a repository that has not been registered
    with the unit of work instance.
    """

    pass
