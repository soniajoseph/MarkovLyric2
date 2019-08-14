"""
	t = typed.int | typed.string
	assert t.test(1)
	assert t.test('foo')
	assert not t.test(True)

	t1 = typed.int | typed.none
	t2 = typed.set(1,2,5) | typed.string
	t3 = typed.number | None
	t4 = typed.date | typed.datetime.format("%Y-%m-%d %H:%M:%S")
	t5 = typed.range(0, 1.5) | typed.int.range(-1, 1) | typed.float.range(4, 5.2) | typed.range('a', 'z')
	t6 = typed.list(typed.string) | typed.list(typed.int)
	t7 = typed.list(typed.string | typed.int)
	t8 = typed.tuple(typed.int, typed.string, typed.bool)
	t9 = typed.dict({'a': typed.bool, 'b': typed.int}) | typed.dict(a=typed.int, b=typed.bool)

	assert 1 == typed.int.cast('1')
	assert '2' == typed.str.cast(2)
	assert datetime.datetime(2012, 12, 12, 12, 12, 12) == typed.datetime.format("%Y-%m-%d %H:%M:%S").cast('2012-12-12 12:12:12')
"""

import types, datetime, itertools

try:
	import ujson as json
	__HAS_UJSON__ = True
except ImportError:
	import json
	__HAS_UJSON__ = False

class O(object):
	pass

python = O()
python.type = type
python.int = int
python.str = str
python.unicode = unicode
python.float = float
python.bool = bool
python.long = long
python.set = set
python.frozenset = frozenset
python.datetime = datetime
python.list = list
python.dict = dict
python.any = any
python.json = json
python.tuple = tuple
python.types = types
python.iter = iter


class Type(object):
	__slots__ = []

	def __init__(self):
		raise Exception('abstract')

	def test(self, obj):
		raise NotImplementedError()

	def make_optional(self):
		return OptionalType(self)

	optional = property(make_optional)

	def default(self, value):
		return DefaultType(self, value)

	def load(self, obj):
		if not self.test(obj):
			raise ValueError('object has invalid type')

		return obj

	def save(self, obj):
		if not self.test(obj):
			raise ValueError('object has invalid type')

		return obj

	def format(self, fmt):
		if isinstance(fmt, python.dict):
			return DictFormatType(self, fmt)
		elif fmt is json:
			return JSONFormatType(self)
		raise NotImplementedError()

	def __or__(self, another_type):
		if another_type is None:
			return UnionType(self, none)
		elif isinstance(another_type, UnionType):
			return UnionType(self, *another_type.types)
		elif isinstance(another_type, Type):
			return UnionType(self, another_type)
		else:
			return NotImplemented


class AnyType(Type):
	__slots__ = []

	def __init__(self):
		pass

	def test(self, obj):
		return True

	def load(self, obj):
		return obj

	def save(self, obj):
		return obj


class PrimitiveType(Type):
	__slots__ = ['type']

	def __init__(self, t):
		self.type = t

	def test(self, obj):
		return isinstance(obj, self.type)


class IntType(Type):
	__slots__ = []
	def __init__(self):
		pass

	def test(self, obj):
		return isinstance(obj, (python.int, python.long)) and not isinstance(obj, python.bool)


class UnionType(Type):
	__slots__ = ['types']

	def __init__(self, *args):
		if len(args) == 1 and not isinstance(args[0], Type):
			args = args[0]
		self.types = args

	def test(self, obj):
		return python.any(t.test(obj) for t in self.types)

	def __or__(self, another_type):
		if another_type is None:
			return UnionType(none, *self.types)
		elif isinstance(another_type, UnionType):
			return UnionType(python.frozenset(self.types + another_type.types))
		else:
			return UnionType(another_type, *self.types)

	def load(self, obj):
		for type in self.types:
			try:
				return type.load(obj)
			except ValueError:
				continue

		raise ValueError('object matches none of the valid types')

	def save(self, obj):
		for type in self.types:
			try:
				return type.save(obj)
			except ValueError:
				continue

		raise ValueError('object matches none of the valid types')


class SetType(Type):
	__slots__ = ['values']

	def __init__(self, values):
		if not isinstance(values, python.frozenset):
			values = python.frozenset(values)
		self.values = values

	def test(self, obj):
		try:
			return obj in self.values
		except TypeError:		# unhashable types
			return False

	def __or__(self, another_type):
		if isinstance(another_type, SetType):
			return SetType(self.values | another_type.values)
		else:
			return super(SetType, self).__or__(another_type)


class DateType(Type):
	__slots__ = []

	def __init__(self):
		pass

	def test(self, obj):
		return isinstance(obj, python.datetime.date) and not isinstance(obj, python.datetime.datetime)

	def format(self, fmt):
		if isinstance(fmt, basestring):
			return DateFormatType(fmt)
		else:
			return super(DateType, self).format(fmt)


class DateFormatType(Type):
	__slots__ = ['fmt']

	def __init__(self, fmt):
		self.fmt = fmt

	def test(self, obj):
		return date.test(obj)

	def load(self, obj):
		try:
			return python.datetime.datetime.strptime(obj, self.fmt).date()
		except TypeError, e:
			raise ValueError(*e.args)

	def save(self, obj):
		if not date.test(obj):
			raise ValueError('object is not a date')

		return obj.strftime(self.fmt)


class DatetimeType(PrimitiveType):
	def __init__(self):
		super(DatetimeType, self).__init__(python.datetime.datetime)

	def format(self, fmt):
		if isinstance(fmt, basestring):
			return DatetimeFormatType(fmt)
		else:
			return super(DatetimeType, self).format(fmt)


class DatetimeFormatType(Type):
	__slots__ = ['fmt']

	def __init__(self, fmt):
		self.fmt = fmt

	def test(self, obj):
		return isinstance(obj, python.datetime.datetime)

	def load(self, obj):
		try:
			return python.datetime.datetime.strptime(obj, self.fmt)
		except TypeError, e:
			raise ValueError(*e.args)

	def save(self, obj):
		if not isinstance(obj, python.datetime.datetime):
			raise ValueError('object is not a datetime')

		return obj.strftime(self.fmt)


class ListType(Type):
	__slots__ = ['type']

	def __init__(self, type):
		self.type = type

	def test(self, obj):
		if not isinstance(obj, python.list):
			return False

		t = self.type
		return all(t.test(el) for el in obj)

	def load(self, obj):
		if not isinstance(obj, python.list):
			raise ValueError('object is not a list')

		t = self.type
		for i in range(len(obj)):
			obj[i] = t.load(obj[i])

		return obj

	def save(self, obj):
		if not isinstance(obj, python.list):
			raise ValueError('object is not a list')

		t = self.type
		for i in range(len(obj)):
			obj[i] = t.save(obj[i])

		return obj


class DictType(Type):
	__slots__ = ['fields', 'trim']

	def __init__(self, fields_dict, trim=False):
		self.fields = fields_dict
		self.trim = trim

	def make_trimmed(self):
		return DictType(self.fields, trim=True)

	trimmed = property(make_trimmed)

	def test(self, obj):
		if not isinstance(obj, python.dict):
			return False

		num = 0
		for field, type in self.fields.iteritems():
			if field in obj:
				value = obj[field]
			else:
				if isinstance(type, OptionalType):
					continue
				return False

			if not type.test(value):
				return False
			num += 1

		if not self.trim and len(obj) > num:
			return False

		return True

	def load(self, obj):
		if not isinstance(obj, python.dict):
			raise ValueError('object is not a dict')

		num = 0
		for field, type in self.fields.iteritems():
			if field in obj:
				value = obj[field]
			else:
				if isinstance(type, DefaultType):
					obj[field] = type.default_value
					num += 1
					continue
				if isinstance(type, OptionalType):
					continue
				raise ValueError('dict is missing field %s' % repr(field))

			obj[field] = type.load(value)
			num += 1

		if len(obj) > num:
			if self.trim:
				for field in obj.keys():
					if not field in self.fields:
						del obj[field]
			else:
				raise ValueError('dict has unexpected fields')

		return obj

	def save(self, obj):
		if not isinstance(obj, python.dict):
			raise ValueError('object is not a dict')

		num = 0
		for field, type in self.fields.iteritems():
			if field in obj:
				value = obj[field]
			else:
				if isinstance(type, OptionalType):
					continue
				raise ValueError('dict is missing field %s' % repr(field))

			if isinstance(type, DefaultType) and value == type.default_value:
				del obj[field]
				continue

			num += 1

			obj[field] = type.save(value)

		if len(obj) > num:
			if self.trim:
				for field in obj.keys():
					if not field in self.fields:
						del obj[field]
			else:
				raise ValueError('dict has additional fields')

		return obj


class OptionalType(Type):
	__slots__ = ['type']

	def __init__(self, type):
		self.type = type

	def test(self, obj):
		return self.type.test(obj)

	def load(self, obj):
		return self.type.load(obj)

	def save(self, obj):
		return self.type.save(obj)

	def format(self, fmt):
		return self.type.format(fmt).optional


class DefaultType(OptionalType):
	__slots__ = ['default_value']

	def __init__(self, type, default_value):
		self.type = type
		self.default_value = default_value

	def format(self, fmt):
		return self.type.format(fmt).default(self.default_value)


class DictFormatType(Type):
	__slots__ = ['type', 'save_dict', 'load_dict']

	def __init__(self, type, save_dict):
		load_dict = {}
		for key, value in save_dict.iteritems():
			load_dict[value] = key

		self.save_dict = save_dict
		self.load_dict = load_dict
		self.type = type

	def test(self, obj):
		return self.type.test(obj)

	def load(self, obj):
		if obj in self.load_dict:
			val = self.load_dict[obj]
		else:
			val = obj
		return self.type.load(val)

	def save(self, obj):
		obj = self.type.save(obj)
		if obj in self.save_dict:
			return self.save_dict[obj]
		else:
			return obj


class JSONFormatType(Type):
	__slots__ = ['type', 'double_precision']

	def __init__(self, type, double_precision=None):
		if double_precision is not None and not __HAS_UJSON__:
			raise NotImplementedError('double_precision is not supported since the `ujson` library is not available for import')
		self.type = type
		self.double_precision = double_precision

	def test(self, obj):
		return self.type.test(obj)

	def load(self, obj):
		return self.type.load(python.json.loads(obj))

	def save(self, obj):
		if self.double_precision is not None:
			return python.json.dumps(self.type.save(obj), double_precision=self.double_precision)
		return python.json.dumps(self.type.save(obj))


class TupleType(Type):
	__slots__ = ['types']

	def __init__(self, types):
		self.types = types

	def test(self, obj):
		if not isinstance(obj, python.tuple):
			return False

		if len(obj) != len(self.types):
			return False

		return all(type.test(item) for type, item in itertools.izip(self.types, obj))

	def load(self, obj):
		if not isinstance(obj, python.tuple):
			raise ValueError('object is not a tuple')

		if len(obj) != len(self.types):
			if len(obj) > len(self.types):
				raise ValueError('too many items')
			else:
				raise ValueError('not enough items')

		return python.tuple(type.load(item) for type, item in itertools.izip(self.types, obj))

	def save(self, obj):
		if not isinstance(obj, python.tuple):
			raise ValueError('object is not a tuple')

		if len(obj) != len(self.types):
			if len(obj) > len(self.types):
				raise ValueError('too many items')
			else:
				raise ValueError('not enough items')

		return python.tuple(type.save(item) for type, item in itertools.izip(self.types, obj))

	def format(self, fmt):
		if fmt is list:
			return ListTupleFormatType(self)
		else:
			return super(TupleType, self).format(fmt)


class ListTupleFormatType(Type):
	__slots__ = ['type']

	def __init__(self, type):
		if not isinstance(type, TupleType):
			raise TypeError('type must be a typed tuple type')

		self.type = type

	def test(self, obj):
		return self.type.test(obj)

	def load(self, obj):
		if not isinstance(obj, python.list):
			raise ValueError('object is not a list')
		return self.type.load(python.tuple(obj))

	def save(self, obj):
		return python.list(self.type.save(obj))








int = integer = IntType()
float = PrimitiveType(python.float)
null = none = PrimitiveType(python.types.NoneType)
ascii = str = PrimitiveType(python.str)
unicode = PrimitiveType(python.unicode)
string = PrimitiveType(basestring)
bool = boolean = PrimitiveType(python.bool)
date = DateType()
datetime = DatetimeType()


def set(*values):
	return SetType(values)

number = num = int | float

def list(type):
	if not isinstance(type, Type):
		raise TypeError('typed.list() argument must be a typed type')

	return ListType(type)

def dict(fields_dict):
	if not isinstance(fields_dict, python.dict):
		raise TypeError('typed.dict() argument must be a python dict')
	if not all(isinstance(field_type, Type) for field_type in fields_dict.itervalues()):
		raise TypeError('typed.dict() argument must have values which are typed types')

	return DictType(fields_dict)

def tuple(*types):
	if not all(isinstance(type, Type) for type in types):
		raise TypeError('typed.tuple() arguments must be typed types')

	return TupleType(types)

any = AnyType()
optional = any.optional

def default(value):
	return any.default(value)

def json(type, **kwargs):
	return JSONFormatType(type, **kwargs)
