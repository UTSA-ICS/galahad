#!/usr/bin/env python

class ExcaliburException(Exception):
	def __init__(self, *args, **kwargs):
		Exception.__init__(self, *args, **kwargs)
		self.retcode = 0
		self.details = None

	def __str__(self):
		s = "ERROR: " + self.__class__.__name__ + " (%d)" % self.retcode
		if self.details:
			s += " " + self.details
		return s


class InvalidOrMissingParameters(ExcaliburException):
	def __init__(self, *args, **kwargs):
		ExcaliburException.__init__(self, *args, **kwargs)
		self.retcode = 1

class UserNotAuthorized(ExcaliburException):
	def __init__(self, *args, **kwargs):
		ExcaliburException.__init__(self, *args, **kwargs)
		self.retcode = 2

class UserTokenExpired(ExcaliburException):
	def __init__(self, *args, **kwargs):
		ExcaliburException.__init__(self, *args, **kwargs)
		self.retcode = 3

class InvalidId(ExcaliburException):
	def __init__(self, *args, **kwargs):
		ExcaliburException.__init__(self, *args, **kwargs)
		self.retcode = 10

class VirtueNotStopped(ExcaliburException):
	def __init__(self, *args, **kwargs):
		ExcaliburException.__init__(self, *args, **kwargs)
		self.retcode = 11

class ServerDestroyError(ExcaliburException):
	def __init__(self, *args, **kwargs):
		ExcaliburException.__init__(self, *args, **kwargs)
		self.retcode = 100

class NotImplemented(ExcaliburException):
	def __init__(self, method_name, *args, **kwargs):
		ExcaliburException.__init__(self, *args, **kwargs)
		self.retcode = 254
		self.details = method_name

class UnspecifiedError(ExcaliburException):
	def __init__(self, *args, **kwargs):
		ExcaliburException.__init__(self, *args, **kwargs)
		self.retcode = 255