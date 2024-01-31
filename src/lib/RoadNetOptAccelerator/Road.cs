using NetTopologySuite.Algorithm;
using NetTopologySuite.Geometries;
using NetTopologySuite.Index.Strtree;
using NetTopologySuite.LinearReferencing;
using NetTopologySuite.Operation.Relate;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;

namespace RoadNetOptAccelerator
{
    public class RoadManager
    {
        public static List<Road> mRoads = new List<Road>();
        public static Guid uuid = new Guid();

        public static Road AddRoad(Coordinate[] coords, RoadLevel roadLevel, RoadState roadState)
        {
            Road road = new Road(coords, roadLevel, roadState);
            mRoads.Add(road);
            RoadManager.uuid = new Guid();
            return road;
        }
        
        public static Road[] AddRoads(List<Coordinate[]> coordsList, RoadLevel[] roadLevels, RoadState[] roadStates)
        {
            Road[] roads = new Road[coordsList.Count];
            for (int i = 0; i < coordsList.Count; i++)
            {
                Coordinate[] coords = coordsList[i];
                RoadLevel roadLevel = roadLevels[i];
                RoadState roadState = roadStates[i];
                roads[i] = AddRoad(coords, roadLevel, roadState);
            }
            return roads;
        }
        public static List<Road> GetAllRoads()
        {
            return mRoads;
        }
        public static void RemoveRoad(Road road)
        {
            road.OnDestroy();
            mRoads.Remove(road);
            RoadManager.uuid = new Guid();
        }

        public static void RemoveAllRoads()
        {
            Road[] roadsToRemove = mRoads.ToArray();
            foreach (Road road in roadsToRemove)
            {
                RemoveRoad(road);
            }
        }

        public static Road GetRoadByUid(Guid uuid)
        {
            List<Road> matchingRoads = mRoads.Where(r => r.uuid == uuid).ToList();
            return matchingRoads.Count > 0 ? matchingRoads[0] : null;
        }

        public static Road GetRoadByIndex(int index)
        {
            return index < mRoads.Count ? mRoads[index] : null;
        }

        public static Road[] GetRoadsByIndexes(int[] indexes)
        {
            return indexes.Select(i => mRoads[i]).ToArray();
        }

        public static List<Road> GetRoadsByLevel(RoadLevel level)
        {
            return mRoads.Where(r => r.roadLevel == level).ToList();
        }
        public static List<Road> GetRoadsByState(RoadState state)
        {
            return mRoads.Where(r => r.roadState == state).ToList();
        }
        public static Coordinate InterpolateRoad(Road road, double distance, bool normalized)
        {
            LengthIndexedLine indexedLine = new LengthIndexedLine(road.lineString);
            if (normalized)
            {
                distance = road.lineString.Length * distance;
            }
            Coordinate coord = indexedLine.ExtractPoint(distance);
            return coord;
        }
        public static List<Road> SplitRoad(Road road, double distance, bool normalized)
        {
            Coordinate coord = InterpolateRoad(road, distance, normalized);
            return SplitRoad(road, coord);
        }

        public static List<Road> SplitRoad(Road road, Coordinate coord)
        {
            LineString lineString = road.lineString;
            LengthIndexedLine indexedLine = new LengthIndexedLine(lineString);
            double length = lineString.Length;
            double index = indexedLine.IndexOf(coord);
            if(index  == 0 || index == length)
            {
                return new List<Road> { road };
            }
            LineString line1 = (LineString)indexedLine.ExtractLine(0,index);
            LineString line2 = (LineString)indexedLine.ExtractLine(index, length);
            Road road1 = AddRoad(line1.Coordinates, road.roadLevel, road.roadState);
            Road road2 = AddRoad(line2.Coordinates, road.roadLevel, road.roadState);
            RemoveRoad(road);
            return new List<Road>() { road1, road2 };
        }

        public static Road MergeRoads(Road road1, Road road2)
        {
            if(road1.roadLevel != road2.roadLevel)
            {
                Console.WriteLine($"road level not match: {road1.roadLevel},{road2.roadLevel} ");
                return null;
            }
            if(road1.roadState != road2.roadState)
            {
                Console.WriteLine($"road state not match: {road1.roadState},{road2.roadState} ");
                return null;
            }
            Node node1u = road1.uNode;
            Node node1v = road1.vNode;
            Node node2u = road2.uNode;
            Node node2v = road2.vNode;
            Coordinate[] coords1 = road1.coords;
            Coordinate[] coords2 = road2.coords;
            if(node1u == node2u)
            {
                // v -- u u -- v
                Array.Reverse(coords1);
            }else if(node1u == node2v)
            {
                // v -- u v -- u
                Array.Reverse(coords1);
                Array.Reverse(coords2);
            }else if(node1v == node2u)
            {
                // u -- v u -- v

            }else if (node1v == node2v)
            {
                // u -- v v -- u
                Array.Reverse(coords2);
            }
            else
            {
                Console.WriteLine("no common node found");
                return null;
            }
            Coordinate[] newCoords = new Coordinate[coords1.Length + coords2.Length];
            Array.Copy(coords1, 0, newCoords, 0, coords1.Length - 1);
            Array.Copy(coords2, 0, newCoords, newCoords.Length - coords2.Length, coords2.Length);
            Road newRoad = AddRoad(newCoords, road1.roadLevel, road1.roadState);
            RemoveRoad(road1);
            RemoveRoad(road2);
            return newRoad;
        }

        public static void SimplifyRoads(Road[] roads)
        {
            HashSet<Road> roadSet = new HashSet<Road>(roads);
            HashSet<Node> relatedNodes = new HashSet<Node>();
            foreach (var road in roadSet)
            {
                relatedNodes.Add(road.uNode);
                relatedNodes.Add(road.vNode);
            }
            foreach (var node in relatedNodes)
            {
                if(node.parentRoads.Count == 2)
                {
                    Road[] parentRoads = node.parentRoads.ToArray();
                    Road parentRoad1 = parentRoads[0];
                    Road parentRoad2 = parentRoads[1];
                    if(!roadSet.Contains(parentRoad1) || !roadSet.Contains(parentRoad2)){continue;}
                    
                    MergeRoads(parentRoad1, parentRoad2);
                }
            }
        }
        public static void SimplifyAllRoads()
        {
            var allNodes = NodeManager.GetAllNodes().ToArray();
            foreach (var node in allNodes)
            {
                if (node.parentRoads.Count == 2)
                {
                    Road[] roads = node.parentRoads.ToArray();
                    MergeRoads(roads[0], roads[1]);
                }
            }
        }
        public static byte[] TriangulateRoads(Road[] roads, Color[] colors, float[] widths )
        {
            return CAccelerator.TriangulatePolylines(roads, colors, widths);
        }
        
        public static Road Test()
        {
            Coordinate coord1 = new Coordinate(0, 0);
            Coordinate coord2 = new Coordinate(1, 0);
            Coordinate[] coords = new Coordinate[] { coord1, coord2 };

            return new Road(coords, RoadLevel.FOOTWAY, RoadState.RAW);
        }

        public static Road Test2()
        {
            return null;
        }

    }
    public class Road
    {
        public Guid uuid;
        public Coordinate[] coords;
        public LineString lineString;
        public RoadLevel roadLevel;
        public RoadState roadState;
        public Node uNode;
        public Node vNode;
        public Envelope envelope;
        public Road(){}
        public Road(Coordinate[] coords, RoadLevel roadLevel, RoadState roadState)
        {
            this.uuid = Guid.NewGuid();
            this.uNode = NodeManager.AddNode(coords[0], this);
            this.vNode = NodeManager.AddNode(coords[coords.Length - 1], this);

            //update coords by node
            coords[0] = this.uNode.coord;
            coords[coords.Length - 1] = this.vNode.coord;
            this.coords = coords;
            this.lineString = new LineString(coords);

            this.roadLevel = roadLevel;
            this.roadState = roadState;
            this.envelope = this.lineString.EnvelopeInternal;
        }

        public Road UpdateCoords(Coordinate[] coords)
        {
            Node orguNode = this.uNode;
            Node orgvNode = this.vNode;
            Node newuNode = NodeManager.AddNode(coords[0]);
            Node newvNode = NodeManager.AddNode(coords[coords.Length - 1]);
            if (orguNode != newuNode)
            {
                this.uNode = newuNode;
                newuNode.RegisterParentRoad(this);
                orguNode.UnregisterparentRoad(this);
                NodeManager.ClearNode(orguNode);
            }
            if (orgvNode != newvNode)
            {
                this.vNode = newvNode;
                newvNode.RegisterParentRoad(this);
                orgvNode.UnregisterparentRoad(this);
                NodeManager.ClearNode(orgvNode);
            }

            coords[0] = this.uNode.coord;
            coords[coords.Length - 1] = this.vNode.coord;
            this.coords = coords;
            this.lineString = new LineString(coords);
            this.envelope = this.lineString.EnvelopeInternal;
            return this;

        }


        public void OnDestroy()
        {
            this.uNode.UnregisterparentRoad(this);
            this.vNode.UnregisterparentRoad(this);
            NodeManager.ClearNode(this.uNode);
            NodeManager.ClearNode(this.vNode);
        }

        public Road ReplaceUNode(Node node)
        {
            Node orguNode = this.uNode;
            if(node == orguNode){return this;}
            this.uNode = node;
            this.uNode.RegisterParentRoad(this);
            orguNode.UnregisterparentRoad(this);
            NodeManager.ClearNode(orguNode);
            this.coords[0] = this.uNode.coord;
            this.lineString = new LineString(this.coords);
            this.envelope = this.lineString.EnvelopeInternal;
            return this;

        }
        public Road ReplaceVNode(Node node)
        {
            Node orgvNode = this.vNode;
            if (node == orgvNode){return this; }
            this.vNode = node;
            this.vNode.RegisterParentRoad(this);
            orgvNode.UnregisterparentRoad(this);
            NodeManager.ClearNode(orgvNode);
            this.coords[this.coords.Length - 1] = this.vNode.coord;
            this.lineString = new LineString(this.coords);
            this.envelope = this.lineString.EnvelopeInternal;
            return this;
        }
        public Road AddUNode(Node node)
        {
            Node orguNode = this.uNode;
            if(node == orguNode) { return this; }
            this.uNode = node;
            this.uNode.RegisterParentRoad(this);
            orguNode.UnregisterparentRoad(this);
            NodeManager.ClearNode(orguNode);
            Coordinate[] newCoords = new Coordinate[this.coords.Length + 1];
            newCoords[0] = this.uNode.coord;
            Array.Copy(this.coords, 0, newCoords, 1, this.coords.Length);
            this.coords = newCoords;
            this.lineString = new LineString(this.coords);
            this.envelope = this.lineString.EnvelopeInternal;
            return this;
        }
        public Road AddVNode(Node node)
        {
            Node orgvNode = this.vNode;
            if(node == orgvNode) { return this; }
            this.vNode = node;
            this.vNode.RegisterParentRoad(this);
            orgvNode.UnregisterparentRoad(this);
            NodeManager.ClearNode(orgvNode);
            Coordinate[] newCoords = new Coordinate[this.coords.Length + 1];
            newCoords[this.coords.Length] = this.vNode.coord;
            Array.Copy(this.coords, 0, newCoords, 0, this.coords.Length);
            this.coords = newCoords;
            this.lineString = new LineString(this.coords);
            this.envelope = this.lineString.EnvelopeInternal;
            return this;
        }

        public int GetIntLevel()
        {
            return (int)this.roadLevel;
        }
        public int GetIntState()
        {
            return (int)this.roadState;
        }
        public Coordinate GetLastCoord()
        {
            return this.coords[this.coords.Length - 1];
        }
        public Vector2 GetLastVector()
        {
            Coordinate from = this.coords[this.coords.Length - 2];
            Coordinate to = this.coords[this.coords.Length - 1];
            Vector2 dir = new Vector2(to.X - from.X, to.Y - from.Y);
            return dir;
        }

    }



    public enum RoadLevel
    {
        TRUNK = 0,
        PRIMARY = 1,
        SECONDARY = 2,
        TERTIARY = 3,
        FOOTWAY = 4,
        UNDEFINED = -1
    }

    public enum RoadState
    {
        RAW = 0,
        MODIFIED = 1,
        OPTIMIZED = 2,
        OPTIMIZING = 3
    }

}

