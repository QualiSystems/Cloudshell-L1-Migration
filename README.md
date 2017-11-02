This is a prototype of the MRV Converter script. The script was written in front of Cloudshell-8.1GA using Python 2.7.10.
The script should get a list of the relevant MRV resource names as input, and it will automatically create new MRV resources for them, move the physical connections from the old resources to the new ones, and then recreate the logical routes that their physical routes go via relevant MRV resources.

Operation notes:
1.	The directory contains a file named “relevant_resources.txt” – write there the relevant MRV resource names, splitted by new line.
2.	Run the script.

Script structure:
1.	For each reservation, the script finds all the logical routes that go through relevant MRV resources and keeps them in dedicated json file
2.	For each relevant old resource, the script creates an equivalent new resource, disconnects the connections from the old resource and connects them to the new one
3.	For each relevant logical route, the script removes the logical route and creates it again, so the physical connection goes via the new resource

The current status is that the script works in simple cases, but I haven’t tested it yet in more complicated ones. In addition, some of the script may be yet refactored and simplified.
