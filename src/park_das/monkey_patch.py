import collections.abc

import aioschedule

# Monkey patch fix tags not working
def tag_fixed(self, *tags):
    """
    Tags the job with one or more unique identifiers.

    Tags must be hashable. Duplicate tags are discarded.

    :param tags: A unique list of ``Hashable`` tags.
    :return: The invoked job instance
    """
    if not all(isinstance(tag, collections.abc.Hashable) for tag in tags):
        raise TypeError('Tags must be hashable')
    self.tags.update(tags)
    return self

aioschedule.Job.tag = tag_fixed

# Monkey patch add convenient method
def on(self, day : str):
    return getattr(self, day)

setattr(aioschedule.Job, "on", on)
