import aioboto3

from asyncrepo.exceptions import ItemNotFoundError
from asyncrepo.repository import Repository, Page, Item


class Buckets(Repository):
    """
    AWS S3 buckets
    """

    def __init__(self, aioboto_session_kwargs: dict = None):
        self.session = aioboto3.Session(**(aioboto_session_kwargs or {}))

    async def list_page(self) -> Page:
        """
        List buckets
        """
        async with self.session.resource("s3") as s3:
            buckets = []
            async for bucket in s3.buckets.all():
                buckets.append(await self._bucket_to_item(bucket))
            return Page(self, buckets)

    async def get(self, identifier: str) -> Item:
        """
        Get a bucket by identifier
        """
        async with self.session.resource("s3") as s3:
            try:
                bucket = await s3.Bucket(identifier)
            except Exception as e:
                if e.__class__.__name__ == "NoSuchBucket":
                    raise ItemNotFoundError(identifier)
                raise

            # The above appears to not always work, so here's a fallback approach:
            # Checking if we can get the creation date is a way to check if the bucket exists
            # I'm assuming all buckets have a creation date and that anyone with access to the bucket
            # can get the creation date
            if not await bucket.creation_date:
                raise ItemNotFoundError(identifier)

            return await self._bucket_to_item(bucket)

    async def _bucket_to_item(self, bucket):
        data = bucket.meta.data
        if data and data.get("CreationDate"):
            data["CreationDate"] = data["CreationDate"].isoformat()
        else:
            data = {
                "Name": bucket.name,
                "CreationDate": (await bucket.creation_date).isoformat(),
            }
        return Item(self, bucket.name, data)
