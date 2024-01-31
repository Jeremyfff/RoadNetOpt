using NetTopologySuite.Geometries;
using NetTopologySuite.Index;
using NetTopologySuite.Index.Strtree;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace RoadNetOptAccelerator
{

    public class NodeManager
    {
        private static List<Node> mNodes = new List<Node>();
        private static Dictionary<Tuple<long, long>, Node> mCoord2Node = new Dictionary<Tuple<long, long>, Node>();
        


        public static Node AddNode(Coordinate coord)
        {
            var key = Common.CoordToKey(coord);
            if (mCoord2Node.ContainsKey(key))
            {
                return mCoord2Node[key];
            }
            Node node = new Node(coord);
            mNodes.Add(node);
            mCoord2Node.Add(key, node);
            return node;
            
        }
        public static Node AddNode(Coordinate coord, Road parentRoad)
        {
            Node node = AddNode(coord);
            node.RegisterParentRoad(parentRoad);
            return node;
        }
        public static void RemoveNode(Node node)
        {
            // 直接强制删除
            // do not use this by yourself
            mNodes.Remove(node);
            var key = Common.CoordToKey(node.coord);
            mCoord2Node.Remove(key);
        }
        public static void ClearNode(Node node)
        {
            //当没有road引用node时，才会删除
            //always use ClearNode to manage your nodes
            if (!node.AnyRoadUsing())
            {
                RemoveNode(node);
            }
        }
        public static Node[] GetAllNodes()
        {
            return mNodes.ToArray();
        }   

        public static Coordinate[] GetAllNodeCoords()
        {
            Coordinate[] coords = mNodes.Select(n => n.coord).ToArray();
            return coords;
        }


        public static void ClearUnusedNodes()
        {
            Node[] copiedNodes = mNodes.ToArray();
            foreach (Node node in copiedNodes)
            {
                ClearNode(node);
            }
        }



        public static Dictionary<int, List<Node>> GetCloseNodesGroup(long labelAddr, long labelLength) {
            int[] labels = Common.NumpyToArray<int>(labelAddr, labelLength);
            Dictionary<int, List<Node>> group = new Dictionary<int, List<Node>>();
            for (int i = 0; i < labels.Length; i++)
            {
                int label = labels[i];
                if(label == -1) { continue; }
                if (!group.Keys.Contains(label)) { group.Add(label, new List<Node>()); }
                group[label].Add(mNodes[i]);
            }
            return group;
        }

        public static void MergeNodes(Node[] nodes)
        {
            double avgX = 0;
            double avgY = 0;
            foreach (Node node in nodes)
            {
                avgX += node.coord.X;
                avgY += node.coord.Y;
            }
            avgX /= nodes.Length;
            avgY /= nodes.Length;

            Node newNode = AddNode(new Coordinate(avgX, avgY));
            foreach (Node node in nodes)
            {
                foreach (var road in node.parentRoads)
                {
                    if (node == road.uNode)
                    {
                        road.ReplaceUNode(newNode);
                    }
                    else if (node == road.vNode)
                    {
                        road.ReplaceVNode(newNode);
                    }
                }
            }
        }

        public static void MergeGroupedNodes(Dictionary<int, List<Node>> group)
        {
            foreach (int label in group.Keys)
            {
                List<Node> nodes = group[label];
                MergeNodes(nodes.ToArray());
            }
        }

        public static Node Test()
        {
            Console.WriteLine("adding my first node");
            Node node1 = AddNode(new Coordinate(0.0, 1.0));
            Console.WriteLine("node1 uid = " + node1.uuid);

            Console.WriteLine("adding my second node");
            Node node2 = AddNode(new Coordinate(1.0, 1.0));
            Console.WriteLine("node2 uid = " + node2.uuid);

            Console.WriteLine("adding my third node");
            Node node3 = AddNode(new Coordinate(1.0001, 1.0));
            Console.WriteLine("node3 uid = " + node3.uuid);

            return node3;

        }

    }
    public class Node
    {
        public Guid uuid;
        public Coordinate coord;
        public HashSet<Road> parentRoads = new HashSet<Road>();
        public Envelope envelope;
        public Node() { }
        public Node(Coordinate coord)
        {
            this.uuid = Guid.NewGuid();
            this.coord = coord;
            this.envelope = new Envelope(coord);
            
        }
        public Node RegisterParentRoad(Road road)
        {
            this.parentRoads.Add(road);
            return this;
        }
        public Node UnregisterparentRoad(Road road)
        {
            this.parentRoads.Remove(road);
            return this;
        }
        public bool AnyRoadUsing()
        {
            return this.parentRoads.Count > 0;
        }

        public byte[] ToNumpyBuffer()
        {
            return Common.CoordToNumpy(this.coord);
        }

    }
}
