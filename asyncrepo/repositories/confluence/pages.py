from asyncrepo.repositories.confluence._content import _Content


class Pages(_Content):
    def __init__(self, *args, **kwargs):
        kwargs.update({'_type': 'page'})
        super().__init__(*args, **kwargs)
