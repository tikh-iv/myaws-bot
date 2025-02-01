from yandex_cloud_ml_sdk import YCloudML

class ImageYandex:
    def __init__(self,
                 folder_id,
                 auth,):
        sdk = YCloudML(
            folder_id=folder_id,
            auth=auth,
        )
        self.model = sdk.models.image_generation("yandex-art")

    def create_image(self,
                     prompt,
                     width_ratio=2,
                     height_ratio=1
                     ):
        self.model = self.model.configure(width_ratio=width_ratio, height_ratio=height_ratio)
        operation = self.model.run_deferred(prompt)
        result = operation.wait()
        return result.image_bytes
