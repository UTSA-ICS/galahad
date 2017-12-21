#!/usr/bin/env python

import web
import virtue

urls = ('/virtue', 'virtue.VirtueHandler')

if __name__ == '__main__':
	app = web.application(urls, globals())
	app.run()
