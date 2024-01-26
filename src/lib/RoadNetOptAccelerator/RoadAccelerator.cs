using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using NetTopologySuite.Geometries;
using NetTopologySuite.Algorithm;
using UnityEngine;

namespace RoadNetOptAccelerator
{
    /// <summary>
    /// 
    /// </summary>
    struct RoadData
    {
        public int idx;
        public LineString lineString;

    }
    /// <summary>
    /// 
    /// </summary>
    public class RoadAccelerator
    {


        /// <summary>
        /// 
        /// </summary>
        /// <param name="bVertices">所有的顶点坐标buffer 4 + 4 byte float32</param>
        /// <param name="bFirst">每条道路的开始顶点信息 4 byte int32</param>
        /// <param name="bNumVerticesPerPolyline">每条道路占用多少顶点 4 byte int32</param>
        /// <param name="bIdxToCalculate">要进行计算的道路index列表  4 byte int32</param>
        public void RoadIntersection(byte[] bVertices, byte[] bFirst, byte[] bNumVerticesPerPolyline, byte[]bIdxToCalculate)
        {

            int inNumPolylines = bFirst.Length / 4;
            int[] inFirst = new int[inNumPolylines];
            int[] inNumVerticesPerPolyline = new int[inNumPolylines];
            RoadData[] roadDatas = new RoadData[inNumPolylines];

            for (int i = 0; i < inNumPolylines; i += 1)
            {   
                int first = BitConverter.ToInt32(bFirst, 4 * i);
                int numVertices = BitConverter.ToInt32(bNumVerticesPerPolyline, 4 * i);
                inFirst[i] = first;
                inNumVerticesPerPolyline[i] = numVertices;

                Coordinate[] vertices = new Coordinate[numVertices];
                for (int j = 0; j < numVertices; j++)
                {   
                    float x = BitConverter.ToSingle(bVertices, 8 * (first + j));
                    float y = BitConverter.ToSingle(bVertices, 8 * (first + j) + 4);
                    vertices[j] = new Coordinate(x, y);
                }
                LineString lineString = new LineString(vertices);
                roadDatas[i] = new RoadData { lineString = lineString, idx = i };
            }

            int inNumPolylinesToCalculate = bIdxToCalculate.Length / 4;
            int[] inIdxToCalculate = new int[inNumPolylinesToCalculate];
            for (int i = 0; i < inNumPolylinesToCalculate; i++)
            {
                inIdxToCalculate[i] = BitConverter.ToInt32(bIdxToCalculate, 4 * i);
            }


            //计算碰撞
            RoadData[] allRoads = roadDatas;
            RoadData[] roadsToCalculate = inIdxToCalculate.Select(index => allRoads[index]).ToArray();

            foreach (RoadData road1 in roadsToCalculate)
            {
                foreach (var road2 in allRoads)
                {
                    LineString line1 = road1.lineString;
                    LineString line2 = road2.lineString;
                    bool isIntersecting = line1.Intersects(line2);

                    if (isIntersecting)
                    {
                        // 计算交点
                        Point intersectionPoint = (Point)line1.Intersection(line2);
                        double x = intersectionPoint.Coordinate.X;
                        double y = intersectionPoint.Coordinate.Y;
                        Console.WriteLine($"Intersection point: ({x}, {y})");
                    }
                }
            }

        }
    }
}
