import aioboto3

from asyncrepo.exceptions import ItemNotFoundError
from asyncrepo.repository import Repository, Page, Item


class S3Objects(Repository):
    """
    AWS S3 Objects
    """

    def __init__(self, bucket_name: str, aioboto_session_kwargs: dict = None):
        self.bucket_name = bucket_name
        self.session = aioboto3.Session(**(aioboto_session_kwargs or {}))

    async def list_page(self, *args, **kwargs) -> 'Page':
        """
        List objects
        """
        return await self.search_page(*args, **kwargs)

    async def search_page(self, query='', _iterator=None, **kwargs) -> 'Page':
        """
        Search for objects by prefix
        """
        async with self.session.resource("s3") as s3:
            if _iterator is None:
                paginator = s3.meta.client.get_paginator("list_objects")
                _iterator = paginator.paginate(Bucket=self.bucket_name, Prefix=query)
            async for page in _iterator:
                objects = [await self._object_to_item(obj) for obj in page.get("Contents", [])]
                next_page_fn = None
                if page.get("IsTruncated"):
                    async def next_page_fn():
                        return await self.search_page(query, _iterator=_iterator)
                return Page(self, objects, next_page_fn)


    async def get(self, identifier: str) -> Item:
        """
        Get an object by identifier
        """
        async with self.session.resource("s3") as s3:
            try:
                obj = await s3.Object(self.bucket_name, identifier)
                return await self._object_to_item(obj)
            except Exception as e:
                if hasattr(e, "response") and e.response["Error"]["Code"] == "404":
                    raise ItemNotFoundError(identifier)
                raise


    async def _object_to_item(self, obj) -> Item:
        if isinstance(obj, dict):
            data = {
                "Key": obj["Key"],
                "LastModified": obj["LastModified"].isoformat(),
                "Size": obj["Size"],
                "ETag": obj["ETag"],
                "StorageClass": obj["StorageClass"],
            }
        else:
            data = {
                "Key": obj.key,
                "LastModified": (await obj.last_modified).isoformat(),
                "Size": await obj.content_length,
                "ETag": await obj.e_tag,
                "StorageClass": await obj.storage_class,
            }
        return Item(self, data["Key"], data)
