using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using NetTopologySuite.Geometries;
using NetTopologySuite.Algorithm;
using NetTopologySuite.Index.Strtree;
using System.Diagnostics;
using System.Threading;
using NetTopologySuite.Index.HPRtree;
using NetTopologySuite.LinearReferencing;
using UnityEngine;
using NetTopologySuite.Index.Quadtree;

namespace RoadNetOptAccelerator
{

    struct RoadData
    {
        public int idx;
        public LineString lineString;
        public Envelope bbox;

    }
    /// <summary>
    /// 
    /// </summary>
    public class RoadAccelerator
    {

        static int mMaxChunks = 8;
        static int mMinGeoPerChunk = 1;

        /// <summary>
        /// 设置最大并行计算线程数
        /// </summary>
        /// <param name="num"></param>
        public static void SetMaxChunks(int num)
        {
            mMaxChunks = num;
        }

        /// <summary>
        /// 设置每个计算线程分配到的最少的几何体数量
        /// </summary>
        /// <param name="num"></param>
        public static void SetMinGeoPerChunk(int num)
        {
            mMinGeoPerChunk = num;
        }

        /// <summary>
        /// 
        /// </summary>
        public static void DataInputTest(long address, long length)
        {   
            Console.WriteLine("c# get data");
            Console.WriteLine($"address = {address}, length = {length}");
            Stopwatch stopwatch = new Stopwatch();
            stopwatch.Start();
            float[] array = Common.NumpyToArray<float>(address, length);
            stopwatch.Stop();
            Console.WriteLine("array length: " + array.Length);
            Console.WriteLine("exec time: " + stopwatch.Elapsed);
        }

        /// <summary>
        /// 批量计算道路相交
        ///  returns:
        ///   idx1    | idx2   | x      | y
        ///   int32   | int32  | float32| float32
        ///   4 bytes | 4 bytes| 4 bytes| 4 bytes 
        /// </summary>
        /// <param name="addrVerticesX">顶点坐标x的内存地址</param>
        /// <param name="lenVerticesX">顶点坐标x的个数</param>
        /// <param name="addrVerticesY">顶点坐标y的内存地址</param>
        /// <param name="lenVerticesY">顶点坐标y的个数</param>
        /// <param name="addrFirst">记录了polyline起始点的index序号的array的内存地址</param>
        /// <param name="lenFirst">记录了polyline起始点的index序号的array的长度， 即polyline的个数</param>
        /// <param name="addrNumVerticesPerPolyline">记录了每个polyline顶点个数的array的内存地址</param>
        /// <param name="lenNumVerticesPerPolyline">记录了每个polyline顶点个数的array的长度， 即polyline的个数</param>
        /// <param name="addrIdxToCalculate">记录了哪些idx的polyline需要参与交点计算的array的内存地址</param>
        /// <param name="lenIdxToCalculate">记录了哪些idx的polyline需要参与交点计算的array的长度， 即需要计算的polyline的个数</param>
        public static byte[] RoadIntersection(long addrVerticesX,                long lenVerticesX,
                                              long addrVerticesY,                long lenVerticesY,
                                              long addrFirst,                    long lenFirst,
                                              long addrNumVerticesPerPolyline,   long lenNumVerticesPerPolyline,
                                              long addrIdxToCalculate,           long lenIdxToCalculate)
        {
//            Stopwatch stopwatch = new Stopwatch();
//            Stopwatch intersectionStopWatch = new Stopwatch();
//            Stopwatch intersectsFuncStopWatch = new Stopwatch();
//            stopwatch.Start();

            List<Coordinate[]> coordsList = Common.NumpyToCoordsList(addrVerticesX, lenVerticesX, addrVerticesY, lenVerticesY, addrFirst, lenFirst, addrNumVerticesPerPolyline, lenNumVerticesPerPolyline);
            int[] inIdxToCalculate = Common.NumpyToArray<int>(addrIdxToCalculate, lenIdxToCalculate);
            int inNumPolylines = coordsList.Count();
            RoadData[] roadDatas = new RoadData[inNumPolylines];
            STRtree<RoadData> spatialIndex = new STRtree<RoadData>();
            for (int i = 0; i < inNumPolylines; i += 1)
            {
                Coordinate[] vertices = coordsList[i];
                LineString lineString = new LineString(vertices);
                Envelope bbox = lineString.EnvelopeInternal;
                RoadData roadData = new RoadData { lineString = lineString, idx = i, bbox = bbox };
                roadDatas[i] = roadData;
                spatialIndex.Insert(bbox, roadData);
            }
//            stopwatch.Stop();
//            Console.WriteLine("[step 1] prepare data time: " + stopwatch.Elapsed);
//            stopwatch.Restart();

            //计算碰撞
            RoadData[] roadsToCalculate = inIdxToCalculate.Select(index => roadDatas[index]).ToArray();
            List<RoadData[]> chunks = Common.SplitArray(roadsToCalculate, mMaxChunks, mMinGeoPerChunk);
//            Console.WriteLine($"Parallel Chunks = {chunks.Count}");
            HashSet<Tuple<int, int>> calculatedIdxPair = new HashSet<Tuple<int, int>>();
            List<byte> outDataList = new List<byte>();
            // 并行处理每个部分
            Parallel.ForEach(chunks, chunk =>
            {
                List<byte> chunkDataList = new List<byte>();
                foreach (RoadData road1 in chunk)
                {
                    IList<RoadData> candidates = spatialIndex.Query(road1.bbox);
                    foreach (var road2 in candidates)
                    {
                        if (road1.idx == road2.idx){continue;}
                        Tuple<int, int> pair = new Tuple<int, int>(road1.idx, road2.idx);
                        Tuple<int, int> rpair = new Tuple<int, int>(road2.idx, road1.idx);
                        lock (calculatedIdxPair) { if (calculatedIdxPair.Contains(pair)) { continue; } else { calculatedIdxPair.Add(pair); calculatedIdxPair.Add(rpair); } }

                        LineString line1 = road1.lineString;
                        LineString line2 = road2.lineString;

//                        intersectsFuncStopWatch.Start();
                        bool isIntersecting = line1.Intersects(line2);
//                        intersectsFuncStopWatch.Stop();
                        if (!isIntersecting){continue;}

//                        intersectionStopWatch.Start();
                        Geometry intersectionResult = line1.Intersection(line2);
//                        intersectionStopWatch.Stop();
                        List<Point> pointResults = new List<Point>();
                        if (intersectionResult is Point)
                        {
                            pointResults.Add((Point)intersectionResult);
                        }
                        else if(intersectionResult is MultiPoint)
                        {
                            foreach (Point point in (MultiPoint)intersectionResult){pointResults.Add(point);}
                        }
                        else{ }
                        foreach (Point point in pointResults)
                        {
                            double x = point.Coordinate.X;
                            double y = point.Coordinate.Y;
                            chunkDataList.AddRange(BitConverter.GetBytes(road1.idx)); // 4 bytes
                            chunkDataList.AddRange(BitConverter.GetBytes(road2.idx)); // 4 bytes
                            chunkDataList.AddRange(BitConverter.GetBytes((float)x)); // 4 bytes
                            chunkDataList.AddRange(BitConverter.GetBytes((float)y)); // 4 bytes
                        }
                    }
                }
                lock (outDataList) { outDataList.AddRange(chunkDataList); };
            });
//            stopwatch.Stop();
//            Console.WriteLine("[step 2] calculate intersection time: " + stopwatch.Elapsed);
//            Console.WriteLine("  -Intersects func time: " + intersectsFuncStopWatch.Elapsed);
//            Console.WriteLine("  -Intersection func time: " + intersectionStopWatch.Elapsed);
//            Console.WriteLine("C# complete");
            return outDataList.ToArray();
        }


        /// <summary>
        /// 根据若干点分割一条路
        /// </summary>
        /// <param name="addrVerticesX"></param>
        /// <param name="lenVerticesX"></param>
        /// <param name="addrVerticesY"></param>
        /// <param name="lenVerticesY"></param>
        /// <param name="addrSplitPtX"></param>
        /// <param name="lenSplitPtX"></param>
        /// <param name="addrSplitPtY"></param>
        /// <param name="lenSplitPtY"></param>
        /// <returns>
        /// Tuple <all coords, num coords per polyline>
        /// </returns>
        public static Tuple<byte[], byte[]> SplitRoad(
            long addrVerticesX, long lenVerticesX,
            long addrVerticesY, long lenVerticesY,
            long addrSplitPtX, long lenSplitPtX,
            long addrSplitPtY, long lenSplitPtY
            )
        {
            
            Coordinate[] vertices = Common.NumpyToCoords(addrVerticesX, lenVerticesX, addrVerticesY, lenVerticesY);
            Coordinate[] splitPts = Common.NumpyToCoords(addrSplitPtX, lenSplitPtX, addrSplitPtY, lenSplitPtY);
            LineString lineString = new LineString(vertices);
            LengthIndexedLine indexedLine = new LengthIndexedLine(lineString);
            double length = lineString.Length;

            List<double> indexes = new List<double>();
            foreach (var splitPt in splitPts)
            {
                double index = indexedLine.IndexOf(splitPt);
                if(index == 0 || index == length){continue; }
                indexes.Add(index);
            }
            indexes.Add(0);
            indexes.Add(length);
            List<double> distinctIndexes = indexes.Distinct().ToList();  //去重
            distinctIndexes.Sort();
            List<Coordinate[]> coordsList = new List<Coordinate[]>();
            for (int i = 0; i < distinctIndexes.Count - 1; i++)
            {
                LineString subLineString = (LineString)indexedLine.ExtractLine(distinctIndexes[i], distinctIndexes[i + 1]);
                coordsList.Add(subLineString.Coordinates);
            }
            return Common.CoordsListToNumpy(coordsList);
        }


        public static Tuple<byte[], byte[]> Test()
        {
            byte[] a = BitConverter.GetBytes(1);
            byte[] b = BitConverter.GetBytes(2);
            var result = new Tuple<byte[], byte[]>(a, b);
            return result;
        }
    }
}
