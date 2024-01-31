
using System;
using System.Linq;
using System.Collections;
using System.Runtime.CompilerServices;
using System.Collections.Generic;
using Poly2Tri;
using Poly2Tri.Triangulation.Polygon;
using Poly2Tri.Triangulation.Delaunay;
using System.Threading.Tasks;
using System.Diagnostics.Eventing.Reader;
using System.Runtime.InteropServices;
using System.Diagnostics;

namespace RoadNetOptAccelerator
{
    /// <summary>
    /// 加速类
    /// </summary>
    public class CAccelerator
    {
        static int mMaxChunks = 8;
        static int mMinGeoPerChunk = 4;

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
        struct PointData
        {
            public Vector2 coord;
            public Color color;
            public float radius;
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
        public static byte[] TriangulatePolylines(byte[] bVertices, byte[] bFirst, byte[] bNumVerticesPerPolyline, byte[] bColors, byte[] bWidths)
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

            PolylineData[] polylineDatas = new PolylineData[inNumPolylines];

            
            for (int i = 0; i < inNumPolylines; i++)
            {
                //对于每一条polyline
                int numVertices = inNumVerticesPerPolyline[i];
                Vector2[] vertices = new Vector2[numVertices];
                for (int j = 0; j < numVertices; j++)
                {
                    vertices[j] = inVertices[j + inFirst[i]];
                }
                polylineDatas[i] = new PolylineData { vertices = vertices, width = inWidths[i], color = inColors[i] };
            }

            List<byte> outDataList = new List<byte>();
            for (int i = 0; i < inNumPolylines; i++)
            {
                outDataList.AddRange(TriangulatePolyline(polylineDatas[i]));
            }
            byte[] bOutData = outDataList.ToArray();

            return bOutData;

        }

        public static byte[] TriangulatePolylines(long addrVerticesX, long lenVerticesX, long addrVerticesY, long lenVerticesY,long addrFirst, long lenFirst,long addrNum, long lenNum,long addrColorsR, long lenColorsR,long addrColorsG, long lenColorsG,long addrColorsB, long lenColorsB,long addrColorsA, long lenColorsA,long addrWidths, long lenWidths)
        {
            List<Vector2[]> coordsList = Common.NumpyToVector2List(addrVerticesX, lenVerticesX, addrVerticesY, lenVerticesY, addrFirst, lenFirst, addrNum, lenNum);
            Color[] colors = Common.NumpyToColors(addrColorsR, lenColorsR, addrColorsG, lenColorsG, addrColorsB, lenColorsB, addrColorsA, lenColorsA);
            float[] widths = Common.NumpyToArray<float>(addrWidths, lenWidths);


            List<byte> outDataList = new List<byte>();
            for (int i = 0; i < coordsList.Count; i++)
            {
                outDataList.AddRange(TriangulatePolyline(coordsList[i], widths[i], colors[i]));
            }
            byte[] bOutData = outDataList.ToArray();
            return bOutData;
        }

        public static byte[] TriangulatePolylines(Road[] roads, Color[] colors, float[] widths)
        {
            List<byte> outDataList = new List<byte>();
            for (int i = 0; i < roads.Length; i++)
            {
                Road road = roads[i];
                Color color = colors[i];
                float width = widths[i];
                Vector2[] vertices = Common.CoordsToVector2(road.coords);
                outDataList.AddRange(TriangulatePolyline(vertices, width, color));
            }
            return outDataList.ToArray();
        }
        
        /// <summary>
        /// 将输入的polygon 进行三角剖分，并返回顶点数据
        /// </summary>
        /// <param name="bVertices">所有顶点的xy坐标(float32, float32) 4 + 4 bytes</param>
        /// <param name="bFirst">每个多边形的第一个顶点的编号(int32) 4 bytes </param>
        /// <param name="bNumVerticesPerPolygon">每个多边形的顶点数(int32) 4 bytes </param>
        /// <param name="bColors">每个多边形的颜色(float32, float32, float32, float32) 4 + 4 + 4 + 4 bytes</param>
        /// <returns></returns>
        public static byte[] TriangulatePolygons(byte[] bVertices, byte[] bFirst, byte[] bNumVerticesPerPolygon, byte[] bColors)
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
            List<PolygonData[]> polygonChunks = Common.SplitArray(polygonDatas, mMaxChunks, mMinGeoPerChunk);
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

        public static byte[] TriangulatePolygons(long addrVerticesX, long lenVerticesX, long addrVerticesY, long lenVerticesY, long addrFirst, long lenFirst, long addrNum, long lenNum, long addrColorsR, long lenColorsR, long addrColorsG, long lenColorsG, long addrColorsB, long lenColorsB, long addrColorsA, long lenColorsA)
        {

            List<Vector2[]> coordsList = Common.NumpyToVector2List(addrVerticesX, lenVerticesX, addrVerticesY, lenVerticesY, addrFirst, lenFirst, addrNum, lenNum);
            Color[] colors = Common.NumpyToColors(addrColorsR, lenColorsR, addrColorsG, lenColorsG, addrColorsB, lenColorsB, addrColorsA, lenColorsA);
            
            List<byte> outDataList = new List<byte>();
            for (int i = 0; i < coordsList.Count; i++)
            {
                outDataList.AddRange(TriangulatePolygon(coordsList[i],  colors[i]));
            }
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
        public static byte[] TriangulatePoints(byte[] bVertices, byte[] bColors, byte[] bWidths)
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

        public static byte[] TriangulatePoints(long addrVerticesX, long lenVerticesX, long addrVerticesY, long lenVerticesY, long addrColorsR, long lenColorsR, long addrColorsG, long lenColorsG, long addrColorsB, long lenColorsB, long addrColorsA, long lenColorsA, long addrWidths, long lenWidths)
        {
            Vector2[] coords = Common.NumpyToVector2(addrVerticesX, lenVerticesX, addrVerticesY, lenVerticesY);
            Color[] colors = Common.NumpyToColors(addrColorsR, lenColorsR, addrColorsG, lenColorsG, addrColorsB, lenColorsB, addrColorsA, lenColorsA);
            float[] widths = Common.NumpyToArray<float>(addrWidths, lenWidths);

            List<byte> outDataList = new List<byte>();
            for (int i = 0; i < coords.Length; i++)
            {
                outDataList.AddRange(TriangulatePoint(coords[i], widths[i], colors[i]));
            }
            byte[] bOutData = outDataList.ToArray();
            return bOutData;
        }


        private static byte[] TriangulatePolyline(Vector2[] vertices, float width, Color color)
        {
            int numVertices = vertices.Length;
            if (numVertices == 1)
            {
                return TriangulatePoint(vertices[0], width / 2f, color);
            }
            Vector2[] vertices1 = OffsetLine(vertices, width / 2f);
            Vector2[] vertices2 = OffsetLine(vertices, -width / 2f);

            int outNumVertices = (numVertices - 1) * 6;
            Vector2[] outVertices = new Vector2[outNumVertices];

            for (int j = 0; j < numVertices - 1; j++)
            {
                outVertices[6 * j] = vertices1[j];
                outVertices[6 * j + 1] = vertices1[j + 1];
                outVertices[6 * j + 2] = vertices2[j];
                outVertices[6 * j + 3] = vertices2[j];
                outVertices[6 * j + 4] = vertices1[j + 1];
                outVertices[6 * j + 5] = vertices2[j + 1];
            }
            byte[] outData = GetVerticesData(outVertices, color);
            return outData;
        }

        private static byte[] TriangulatePolyline(PolylineData polylineData)
        {
            return TriangulatePolyline(polylineData.vertices, polylineData.width, polylineData.color);
        }

        private static byte[] TriangulatePoint(Vector2 coord, float radius, Color color, int division = 8)
        {
            Vector2[] circleCoords = new Vector2[division];
            for (int i = 0; i < division; i++)
            {
                double angle = i * Math.PI * 2.0f / division;
                double x = coord.x + Math.Cos(angle) * radius;
                double y = coord.y + Math.Sin(angle) * radius;
                circleCoords[i] = new Vector2((float)x, (float)y);
            }
            int numVertices = division * 3;
            Vector2[] outVertices = new Vector2[numVertices];
 
            for (int i = 0; i < division; i++)
            {
                outVertices[3 * i + 0] = coord;
                outVertices[3 * i + 1] = circleCoords[i];
                outVertices[3 * i + 2] = circleCoords[(i + 1) % division];
            }
            byte[] outData = GetVerticesData(outVertices, color);
            return outData;
        }

        private static byte[] TriangulatePoint(PointData pointdata)
        {
            return TriangulatePoint(pointdata.coord, pointdata.radius, pointdata.color);
        }
        private static byte[] TriangulatePolygon(Vector2[] vertices, Color color)
        {
            if(vertices.Length < 4)
                return null;

            PolygonPoint[] points = new PolygonPoint[vertices.Length];
            for (int i = 0; i < vertices.Length; i++)
            {
                points[i] = new PolygonPoint(vertices[i].x, vertices[i].y);
            }
            Polygon polygon = new Polygon(points);
            try
            {
                P2T.Triangulate(polygon);
                DelaunayTriangle[] triangles = polygon.Triangles.ToArray();
                Vector2[] outVertices = new Vector2[triangles.Length * 3];
                for (int i = 0; i < triangles.Length; i++)
                {
                    var tri = triangles[i];
                    outVertices[3 * i + 0] = new Vector2((float)tri.Points[0].X, (float)tri.Points[0].Y);
                    outVertices[3 * i + 1] = new Vector2((float)tri.Points[1].X, (float)tri.Points[1].Y);
                    outVertices[3 * i + 2] = new Vector2((float)tri.Points[2].X, (float)tri.Points[2].Y);
                }
                byte[] outData = GetVerticesData(outVertices, color);
                return outData;
            }
            catch
            {
                return new byte[0];
            }

        }
        private static byte[] TriangulatePolygon(PolygonData polygonData)
        {
            return TriangulatePolygon(polygonData.vertices, polygonData.color);
        }

        private static unsafe byte[] GetVerticesData(Vector2[] vertices, Color color)
        {
            byte[] outData = new byte[vertices.Length * 24]; // 每个顶点有两个float和一个Color，每个float和Color中的每个分量都占4个字节

            fixed (byte* pOutData = outData)
            {
                float* pFloat = (float*)pOutData;

                for (int i = 0; i < vertices.Length; i++)
                {
                    pFloat[i * 6] = vertices[i].x;
                    pFloat[i * 6 + 1] = vertices[i].y;
                    pFloat[i * 6 + 2] = color.r;
                    pFloat[i * 6 + 3] = color.g;
                    pFloat[i * 6 + 4] = color.b;
                    pFloat[i * 6 + 5] = color.a;
                }
            }

            return outData;
        }

        private static unsafe byte[] GetVerticesListData(List<Vector2[]> verticesList, Color[] colors)
        {
            int totalVertices = verticesList.Sum(vertices => vertices.Length);

            byte[] outVerticesBuffer = new byte[totalVertices * 24]; // x, y, r, g, b, a

            fixed (byte* pOutVerticesBuffer = outVerticesBuffer)
            {
                float* pFloat = (float*)pOutVerticesBuffer;

                int ptrOffset = 0;
                for (int i = 0; i < verticesList.Count; i++)
                {
                    Color color = colors[i];
                    Vector2[] vertices = verticesList[i];
                    for (int j = 0; j < vertices.Length; j++)
                    {
                        pFloat[ptrOffset + j * 6] = vertices[j].x;
                        pFloat[ptrOffset + j * 6 + 1] = vertices[j].y;
                        pFloat[ptrOffset + j * 6 + 2] = color.r;
                        pFloat[ptrOffset + j * 6 + 3] = color.g;
                        pFloat[ptrOffset + j * 6 + 4] = color.b;
                        pFloat[ptrOffset + j * 6 + 5] = color.a;
                    }

                    ptrOffset += vertices.Length * 24;
                }
            }

            return outVerticesBuffer;
        }

        private static Vector2[] OffsetLine(Vector2[] points, float distance)
        {
            Vector2[] offsetPoints = new Vector2[points.Length];
            for (int i = 0; i < points.Length; i++)
            {
                Vector2 direction = (i == 0) ? (points[i + 1].subtract(points[i])).normalize() : (points[i].subtract(points[i - 1])).normalize();
                Vector2 offset = new Vector2(-direction.y * distance, direction.x * distance);
                offsetPoints[i] = points[i].add(offset);
            }
            return offsetPoints;
        }
    }


}
