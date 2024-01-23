
using System;
using System.Linq;
using System.Collections;
using System.Runtime.CompilerServices;
using UnityEngine;
using System.Collections.Generic;
using UnityEngine.Rendering;
using Poly2Tri;
using Poly2Tri.Triangulation.Polygon;
using Poly2Tri.Triangulation.Delaunay;
using System.Threading.Tasks;

namespace RoadNetOptAccelerator
{
    /// <summary>
    /// 加速类
    /// </summary>
    public class CAccelerator
    {
        int mMaxChunks = 8;
        int mMinGeoPerChunk = 4;
        /// <summary>
        /// 加法，测试用
        /// </summary>
        /// <param name="a"></param>
        /// <param name="b"></param>
        /// <returns></returns>
        public Vector3 Add(int a, int b)
        {
            Console.WriteLine($"test a={a} b={b}");
            return new Vector3(a, b, 0);
        }

        /// <summary>
        /// 设置最大并行计算线程数
        /// </summary>
        /// <param name="num"></param>
        public void SetMaxChunks(int num)
        {
            mMaxChunks = num;
        }

        /// <summary>
        /// 设置每个计算线程分配到的最少的几何体数量
        /// </summary>
        /// <param name="num"></param>
        public void SetMinGeoPerChunk(int num)
        {
            mMinGeoPerChunk = num;
        }

        struct PolylineData
        {
            public Vector2[] vertices;
            public Color color;
            public float width;
        }
        struct PolygonData
        {
            public Vector2[] vertices;
            public Color color;
        }


        /// <summary>
        /// 将输入的polyline 变为有宽度的三角顶点，并返回顶点数据
        /// </summary>
        /// <param name="bVertices"> 所有顶点的xy坐标(float32, float32) 4 + 4 bytes</param>
        /// <param name="bFirst">每组折线的第一个顶点的编号(int32) 4 bytes </param>
        /// <param name="bNumVerticesPerPolyline">每组折线的顶点数(int32) 4 bytes </param>
        /// <param name="bColors">每组折线的颜色(float32, float32, float32, float32) 4 + 4 + 4 + 4 bytes</param>
        /// <param name="bWidths">每组折线的宽度(float32) 4 bytes </param>
        /// <returns>赋予宽度并三角化后的顶点数据
        /// (x      , y      , r      , g      , b      , a      )
        /// (float32, float32, float32, float32, float32, float32)
        /// (4      , 4      , 4      , 4      , 4      , 4      )bytes
        /// </returns>
        public byte[] TriangulatePolylines(byte[] bVertices, byte[] bFirst, byte[] bNumVerticesPerPolyline, byte[] bColors, byte[] bWidths)
        {
            int inNumVertices = bVertices.Length / 8;
            int inNumPolylines = bFirst.Length / 4;

            Vector2[] inVertices = new Vector2[inNumVertices];
            int[] inFirst = new int[inNumPolylines];
            int[] inNumVerticesPerPolyline = new int[inNumPolylines];
            Color[] inColors = new Color[inNumPolylines];
            float[] inWidths = new float[inNumPolylines];


            for (int i = 0; i < inNumVertices; i++)
            {
                float x = BitConverter.ToSingle(bVertices, 8 * i);
                float y = BitConverter.ToSingle(bVertices, 8 * i + 4);
                inVertices[i] = new Vector2(x, y);
            }
            for (int i = 0; i < inNumPolylines; i += 1)
            {
                inFirst[i] = BitConverter.ToInt32(bFirst, 4 * i);
                inNumVerticesPerPolyline[i] = BitConverter.ToInt32(bNumVerticesPerPolyline, 4 * i);
                float r = BitConverter.ToSingle(bColors, 16 * i);
                float g = BitConverter.ToSingle(bColors, 16 * i + 4);
                float b = BitConverter.ToSingle(bColors, 16 * i + 8);
                float a = BitConverter.ToSingle(bColors, 16 * i + 12);
                inColors[i] = new Color(r, g, b, a);
                inWidths[i] = BitConverter.ToSingle(bWidths, 4 * i);
            }

            List<byte> outDataList = new List<byte>();
            for (int i = 0; i < inNumPolylines; i++)
            {
                //对于每一条polyline
                int numVertices = inNumVerticesPerPolyline[i];
                if(numVertices > 1)
                {
                    // if it is polyline
                    Vector2[] vertices = new Vector2[numVertices];
                    for (int j = 0; j < numVertices; j++)
                    {
                        vertices[j] = inVertices[j + inFirst[i]];
                    }
                    outDataList.AddRange(TriangulatePolyline(vertices, inWidths[i], inColors[i]));
                    //outDataList.AddRange(TriangulatePoint(vertices[0], inWidths[i], inColors[i]));
                    //outDataList.AddRange(TriangulatePoint(vertices[numVertices - 1], inWidths[i], inColors[i]));
                }
                else if(numVertices == 1)
                {
                    // if it it a point
                    outDataList.AddRange(TriangulatePoint(inVertices[inFirst[i]], inWidths[i], inColors[i]));
                }
            }
            byte[] bOutData = outDataList.ToArray();

            return bOutData;

        }

        /// <summary>
        /// 将输入的polygon 进行三角剖分，并返回顶点数据
        /// </summary>
        /// <param name="bVertices">所有顶点的xy坐标(float32, float32) 4 + 4 bytes</param>
        /// <param name="bFirst">每个多边形的第一个顶点的编号(int32) 4 bytes </param>
        /// <param name="bNumVerticesPerPolygon">每个多边形的顶点数(int32) 4 bytes </param>
        /// <param name="bColors">每个多边形的颜色(float32, float32, float32, float32) 4 + 4 + 4 + 4 bytes</param>
        /// <returns></returns>
        public byte[] TriangulatePolygons(byte[] bVertices, byte[] bFirst, byte[] bNumVerticesPerPolygon, byte[] bColors)
        {

            //解析byte数据
            int inNumVertices = bVertices.Length / 8;
            int inNumPolygons = bFirst.Length / 4;

            Vector2[] inVertices = new Vector2[inNumVertices];
            int[] inFirst = new int[inNumPolygons];
            int[] inNumVerticesPerPolygon = new int[inNumPolygons];
            Color[] inColors = new Color[inNumPolygons];


            for (int i = 0; i < inNumVertices; i++)
            {
                float x = BitConverter.ToSingle(bVertices, 8 * i);
                float y = BitConverter.ToSingle(bVertices, 8 * i + 4);
                inVertices[i] = new Vector2(x, y);
            }
            for (int i = 0; i < inNumPolygons; i += 1)
            {
                inFirst[i] = BitConverter.ToInt32(bFirst, 4 * i);
                inNumVerticesPerPolygon[i] = BitConverter.ToInt32(bNumVerticesPerPolygon, 4 * i);
                float r = BitConverter.ToSingle(bColors, 16 * i);
                float g = BitConverter.ToSingle(bColors, 16 * i + 4);
                float b = BitConverter.ToSingle(bColors, 16 * i + 8);
                float a = BitConverter.ToSingle(bColors, 16 * i + 12);
                inColors[i] = new Color(r, g, b, a);
            }

            //创建polygon data
            PolygonData[] polygonDatas = new PolygonData[inNumPolygons];
            for (int i = 0; i < inNumPolygons; i++)
            {
                int numVertices = inNumVerticesPerPolygon[i];
                Vector2[] vertices = new Vector2[numVertices];
                for (int j = 0; j < numVertices; j++)
                {
                    vertices[j] = inVertices[j + inFirst[i]];
                }
                polygonDatas[i] = new PolygonData { vertices = vertices, color = inColors[i] };
            }

            //根据polygon data 进行计算
            List<PolygonData[]> polygonChunks = SplitPolygonData(polygonDatas);
            Console.WriteLine($"Parallel Chunks = {polygonChunks.Count}");
            List<byte> outDataList = new List<byte>();
            // 并行处理每个部分
            Parallel.ForEach(polygonChunks, polygonChunk =>
            {
                List<byte> chunkDataList = new List<byte>();
                foreach (var polygonData in polygonChunk)
                {
                    byte[] outData = TriangulatePolygon(polygonData);
                    if (outData != null)
                        chunkDataList.AddRange(outData);
                }
                lock (outDataList) { outDataList.AddRange(chunkDataList); }; 
            });

            
/*            for (int i = 0; i < polygonDatas.Length; i++)
            {
                byte[] outData = TriangulatePolygon(polygonDatas[i]);
                if (outData != null) { outDataList.AddRange(outData); }
            }*/

            byte[] bOutData = outDataList.ToArray();

            return bOutData;

        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="bVertices"></param>
        /// <param name="bColors"></param>
        /// <param name="bWidths"></param>
        /// <returns></returns>
        public byte[] TriangulatePoints(byte[] bVertices, byte[] bColors, byte[] bWidths)
        {
            int inNumVertices = bVertices.Length / 8;

            Vector2[] inVertices = new Vector2[inNumVertices];
            Color[] inColors = new Color[inNumVertices];
            float[] inWidths = new float[inNumVertices];


            for (int i = 0; i < inNumVertices; i++)
            {
                float x = BitConverter.ToSingle(bVertices, 8 * i);
                float y = BitConverter.ToSingle(bVertices, 8 * i + 4);
                inVertices[i] = new Vector2(x, y);

                float r = BitConverter.ToSingle(bColors, 16 * i);
                float g = BitConverter.ToSingle(bColors, 16 * i + 4);
                float b = BitConverter.ToSingle(bColors, 16 * i + 8);
                float a = BitConverter.ToSingle(bColors, 16 * i + 12);
                inColors[i] = new Color(r, g, b, a);
                inWidths[i] = BitConverter.ToSingle(bWidths, 4 * i);
            }

            List<byte> outDataList = new List<byte>();
            for (int i = 0; i < inNumVertices; i++)
            {
                outDataList.AddRange(TriangulatePoint(inVertices[i], inWidths[i], inColors[i]));
            }
            byte[] bOutData = outDataList.ToArray();

            return bOutData;



        }

        private byte[] TriangulatePolyline(Vector2[] vertices, float width, Color color)
        {

            int numVertices = vertices.Length;
            Vector2[] vertices1 = OffsetLine(vertices, width);
            Vector2[] vertices2 = OffsetLine(vertices, -width);

            int outNumVertices = (numVertices - 1) * 6;
            Vector2[] outVertices = new Vector2[outNumVertices];
            Color[] outColors = new Color[outNumVertices];
            for (int j = 0; j < numVertices - 1; j++)
            {
                outVertices[6 * j] = vertices1[j];
                outVertices[6 * j + 1] = vertices1[j + 1];
                outVertices[6 * j + 2] = vertices2[j];
                outVertices[6 * j + 3] = vertices2[j];
                outVertices[6 * j + 4] = vertices1[j + 1];
                outVertices[6 * j + 5] = vertices2[j + 1];

                outColors[6 * j] = color;
                outColors[6 * j + 1] = color;
                outColors[6 * j + 2] = color;
                outColors[6 * j + 3] = color;
                outColors[6 * j + 4] = color;
                outColors[6 * j + 5] = color;
            }

            byte[] outData = GetVerticesData(outVertices, outColors);
            return outData;
        }

        private byte[] TriangulatePoint(Vector2 coord, float radius, Color color, int division=8)
        {
            Vector2[] circleCoords = new Vector2[division];
            for (int i = 0; i < division; i++)
            {
                float angle = i * Mathf.PI * 2 / division;
                float x = coord.x + Mathf.Cos(angle) * radius;
                float y = coord.y + Mathf.Sin(angle) * radius;
                circleCoords[i] = new Vector2(x, y);
            }
            int numVertices = division * 3;
            Vector2[] outVertices = new Vector2[numVertices];
            Color[] outColors = new Color[numVertices];

            for (int i = 0; i < division; i++)
            {
                outVertices[3 * i + 0] = coord;
                outVertices[3 * i + 1] = circleCoords[i];
                outVertices[3 * i + 2] = circleCoords[(i + 1) % division];
                outColors[3 * i + 0] = color;
                outColors[3 * i + 1] = color;
                outColors[3 * i + 2] = color;
            }

            byte[] outData = GetVerticesData(outVertices, outColors);
            return outData;
        }

        private byte[] TriangulatePolygon(Vector2[] vertices, Color color)
        {
            if(vertices.Length < 4)
                return null;

            List<PolygonPoint> points = new List<PolygonPoint>();
            foreach (Vector2 vertex in vertices)
            {
                points.Add(new PolygonPoint(vertex.x, vertex.y));
            }
            Polygon polygon = new Polygon(points);
            try
            {
                P2T.Triangulate(polygon);
                List<DelaunayTriangle> triangles = polygon.Triangles.ToList();
                Vector2[] outVertices = new Vector2[triangles.Count * 3];
                Color[] outColors = new Color[triangles.Count * 3];
                for (int i = 0; i < triangles.Count; i++)
                {
                    var triangle = triangles[i];
                    outVertices[3 * i + 0] = new Vector2((float)triangle.Points[0].X, (float)triangle.Points[0].Y);
                    outVertices[3 * i + 1] = new Vector2((float)triangle.Points[1].X, (float)triangle.Points[1].Y);
                    outVertices[3 * i + 2] = new Vector2((float)triangle.Points[2].X, (float)triangle.Points[2].Y);
                    outColors[3 * i + 0] = color;
                    outColors[3 * i + 1] = color;
                    outColors[3 * i + 2] = color;
                }
                byte[] outData = GetVerticesData(outVertices, outColors);
                return outData;
            }
            catch
            {
                return null;
            }

        }
        private byte[] TriangulatePolygon(PolygonData polygonData)
        {
            return TriangulatePolygon(polygonData.vertices, polygonData.color);
        }

        private byte[] GetVerticesData(Vector2[] vertices, Color[] colors)
        {
            List<byte> outDataList = new List<byte>();
            for (int i = 0; i < vertices.Length; i++)
            {
                Vector2 v = vertices[i];
                Color c = colors[i];
                outDataList.AddRange(BitConverter.GetBytes(v.x)); // 4 bytes
                outDataList.AddRange(BitConverter.GetBytes(v.y)); // 4 bytes
                outDataList.AddRange(BitConverter.GetBytes(c.r));  // 4 bytes
                outDataList.AddRange(BitConverter.GetBytes(c.g));  // 4 bytes
                outDataList.AddRange(BitConverter.GetBytes(c.b));  // 4 bytes
                outDataList.AddRange(BitConverter.GetBytes(c.a));  // 4 bytes
            }
            return outDataList.ToArray();
        }
        private Vector2[] OffsetLine(Vector2[] points, float distance)
        {
            Vector2[] offsetPoints = new Vector2[points.Length];
            for (int i = 0; i < points.Length; i++)
            {
                Vector2 direction = (i == 0) ? (points[i + 1] - points[i]).normalized : (points[i] - points[i - 1]).normalized;
                Vector2 offset = new Vector2(-direction.y, direction.x) * distance;
                offsetPoints[i] = points[i] + offset;
            }
            return offsetPoints;
        }

        private List<PolygonData[]> SplitPolygonData(PolygonData[] polygonDatas)
        {
            int numChunks = mMaxChunks;
            numChunks = Math.Min(numChunks, polygonDatas.Length / mMinGeoPerChunk);
            if(numChunks  <= 1)
            {
                return new List<PolygonData[]> { polygonDatas };
            }
            int chunkSize = (int)Math.Ceiling((float)polygonDatas.Length / numChunks);
            List<PolygonData[]> chunks = new List<PolygonData[]>();

            int i = 0;
            while (true)
            {
                int offset = i * chunkSize;
                int remianSize = polygonDatas.Length - offset;
                int currentChunkSize = Math.Min(chunkSize, remianSize);
                PolygonData[] chunk = new PolygonData[currentChunkSize];

                Array.Copy(polygonDatas, offset, chunk, 0, currentChunkSize);
                chunks.Add(chunk);
                i++;
                if (remianSize <= chunkSize)
                    break;
            }
            return chunks;

        }

    }


}
