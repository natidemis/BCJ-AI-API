"""
@authors: natidemis
May 2021

File for managing data approperiate for a given user
"""
#pylint: disable=C0103
if __name__ != '__main__':
    from log import logger
    def authenticate_user(fn):
        """
        Method for validating the given user_id.
        If the user exists, fetch data for that 'user' if required.

        Returns
        -------
        Decorator to be applied to a function.
        """
        def decorator(self, *args, **kwargs):
            user_id = kwargs['user_id']
            if user_id in self.users:
                if self.current_user != user_id:
                    self.update_tree_for_user(user_id)
                logger.info('User: %s in database: %s. Auth succeeded.',user_id,self.users)
            else:
                logger.error('User: %s not in database: %s, Auth failed',user_id,self.users)
                raise ValueError('User not available')
            return fn(self, *args, **kwargs)
        return decorator

    def get_or_create_user(fn):
        """
        Method for validating the given user_id.
        If the user exists, fetch data for that 'user' if required.
        Otherwise, create a new user for the given user_id

        Returns
        -------
        Decorator to be applied to a function.
        """
        def decorator(self, *args, **kwargs):
            user_id = kwargs['user_id']
            if user_id in self.users:
                if self.current_user != user_id:
                    self.update_tree_for_user(user_id)
            else:
                try:
                    self.database.insert_user(user_id)
                    logger.info('Inserted user: %s, new user set: %s',user_id,self.users)
                except (TypeError, DuplicateKeyError) as e:
                    logger.error('Inserting user: %s failed for err: %s',user_id, e)
                    raise e
                self.users.add(user_id)
                self.update_tree_for_user(user_id)
            return fn(self, *args, **kwargs)
        return decorator
