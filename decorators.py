
if not __name__ == '__main__':
    import sys
    from db import Database
    db = Database()
    users = db.fetch_users()
    class variables(object):
        def __init__(self, func):
            self._locals = {}
            self.func = func
            self.db = Database()
            self.curr_user = None
        def __call__(self, *args, **kwargs):
            def tracer(frame, event, arg):
                if event=='return':
                    self._locals = frame.f_locals.copy()
                    self.curr_user = self._locals['req']['user_id']
                    print(self._locals)
            # tracer is activated on next call, return or exception
            sys.setprofile(tracer)
            try:
                # trace the function call
                res = self.func(*args, **kwargs)
            finally:
                # disable tracer and replace with old one
                sys.setprofile(None)
            return res

        def clear_locals(self):
            self._locals = {}

        @property
        def locals(self):
            return self._locals