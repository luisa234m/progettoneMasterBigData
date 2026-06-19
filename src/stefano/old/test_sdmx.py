import sdmx
import pandas as pd

class OECDClient:

    def __init__(self):
        self.client = sdmx.Client("OECD")

    def list_datasets(self):
        response = self.client.dataflow()
        return {
            flow_id: str(flow.name)
            for flow_id, flow
            in response.dataflow.items()
        }

    def get_structure(self, dataset_id):
        structure = self.client.datastructure(dataset_id)
        dsd = structure.structure[dataset_id]
        dimensions = [
            dim.id
            for dim in dsd.dimensions.components
        ]
        return dimensions

    def get_data(self, dataset_id, key):
        response = self.client.data(
            resource_id=dataset_id,
            key=key
        )
        return sdmx.to_pandas(response)



client = OECDClient()
"""
datasets = client.list_datasets()
for flow_id, flow in datasets.items():
    print(f"{flow_id} -> {flow}")
"""
#print(datasets)

#dimensions = client.get_structure("OECD.ELS.HD/DSD_SHA@DF_SHA_FP")
#print(dimensions)

resp = client.client.preview_data("OECD.SDD.NAD:DSD_FIN_DASH@DF_7II_INDIC(1.0)")
print(resp)