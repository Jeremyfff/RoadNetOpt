using NetTopologySuite.Geometries;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;

namespace RoadNetOptAccelerator
{

    public struct Vector2
    {
        public float x;
        public float y;
        public Vector2(float x, float y)
        {
            this.x = x;
            this.y = y;
        }

        public Vector2(double x, double y)
        {
            this.x = (float)x;
            this.y = (float)y;
        }

        public Vector2 subtract(Vector2 vec)
        {
            return new Vector2(this.x - vec.x, this.y - vec.y);
        }

        public Vector2 add(Vector2 vec)
        {
            return new Vector2(this.x + vec.x, this.y + vec.y);
        }

        public Vector2 mul(float val)
        {
            return new Vector2(this.x * val, this.y * val);
        }
        public Vector2 normalize()
        {
            float length = Mathf.Sqrt(this.x * this.x + this.y * this.y);
            if(length == 0)
            {
                return new Vector2(0, 0);
            }
            return new Vector2(this.x / length, this.y / length);
        }
    }
    public struct Color
    {
        public float r;
        public float g;
        public float b;
        public float a;
        public Color(float r, float g, float b, float a)
        {
            this.r = r;
            this.g = g;
            this.b = b;
            this.a = a;
        }
    }
    public class Common
    {
        private const int KEY_PRECISION = 1000;

        public static unsafe T[] NumpyToArray<T>(long address, long length) where T: unmanaged
        {
            IntPtr start = new IntPtr(address);
            T[] array = new T[length];
            fixed (T* ptr = array)
            {
                Buffer.MemoryCopy((void*)start, ptr, length * sizeof(T), length * sizeof(T));
            }
            return array;
        }

        public static unsafe T[] NumpyToArray2<T>(long address, long length) where T : unmanaged
        {
            T[] array = new T[length];

            IntPtr ptr = new IntPtr(address);
            int size = sizeof(T);

            for (int i = 0; i < length; i++)
            {
                array[i] = Marshal.PtrToStructure<T>(ptr + i * size);
            }

            return array;
        }
        public static unsafe T[] NumpyToArray3<T>(long address, long length) where T : unmanaged
        {
            T[] array = new T[length];

            fixed (T* pArray = array)
            {
                T* pElement = pArray;
                byte* pAddress = (byte*)address;

                for (int i = 0; i < length; i++)
                {
                    *pElement = *(T*)pAddress;
                    pElement++;
                    pAddress += sizeof(T);
                }
            }

            return array;
        }

        public static byte[] ArrayToNumpy<T>(T[] array) where T : unmanaged
        {
            int sizeOfT = System.Runtime.InteropServices.Marshal.SizeOf(typeof(T));
            byte[] byteArray = new byte[array.Length * sizeOfT];
            Buffer.BlockCopy(array, 0, byteArray, 0, byteArray.Length);
            return byteArray;
        }


        public static byte[] CoordToNumpy(Coordinate coord)
        {
            byte[] outData = new byte[8]; // 每个坐标有两个float，每个float占4个字节

            unsafe
            {
                fixed (byte* pOutData = outData)
                {
                    float* pFloat = (float*)pOutData;
                    pFloat[0] = (float)coord.X;
                    pFloat[1] = (float)coord.Y;
                }
            }

            return outData;
        }
        public static unsafe byte[] CoordsToNumpy(Coordinate[] coords)
        {
            byte[] outData = new byte[coords.Length * 8]; // 每个坐标有两个float，每个float占4个字节

            fixed (byte* pOutData = outData)
            {
                float* pData = (float*)pOutData;

                for (int i = 0; i < coords.Length; i++)
                {
                    pData[i * 2] = (float)coords[i].X;
                    pData[i * 2 + 1] = (float)coords[i].Y;
                }
            }

            return outData;
        }

        public static unsafe Tuple<byte[], byte[]> CoordsListToNumpy(List<Coordinate[]> coordsList)
        {
            int totalCoords = 0;
            foreach (var coords in coordsList)
            {
                totalCoords += coords.Length;
            }

            byte[] outCoordsBuffer = new byte[totalCoords * 8]; // 每个坐标有两个float，每个float占4个字节
            byte[] outNumBuffer = new byte[coordsList.Count * 4]; // 每个int占4个字节

            fixed (byte* pOutCoordsBuffer = outCoordsBuffer, pOutNumBuffer = outNumBuffer)
            {
                float* pCoordsData = (float*)pOutCoordsBuffer;
                int* pNums = (int*)pOutNumBuffer;

                int coordsOffset = 0;

                for (int i = 0; i < coordsList.Count; i++)
                {
                    byte[] coordsData = CoordsToNumpy(coordsList[i]);
                    int numCoords = coordsList[i].Length;

                    Marshal.Copy(coordsData, 0, (IntPtr)(pCoordsData + coordsOffset), coordsData.Length);
                    pNums[i] = numCoords;

                    coordsOffset += numCoords * 2; // 每个坐标占两个float
                }
            }

            return new Tuple<byte[], byte[]>(outCoordsBuffer, outNumBuffer);
        }


        public static Coordinate[] NumpyToCoords(long addressX, long lengthX, long addressY, long lengthY)
        {
            float[] xArr = NumpyToArray<float>(addressX, lengthX);
            float[] yArr = NumpyToArray<float>(addressY, lengthY);

            Coordinate[] coords = new Coordinate[xArr.Length];
            for (int i = 0; i < xArr.Length; i++)
            {
                coords[i] = new Coordinate(xArr[i], yArr[i]);
            }
            return coords;
        }
        
        public static Vector2[] NumpyToVector2(long addressX, long lengthX, long addressY, long lengthY)
        {
            float[] xArr = NumpyToArray<float>(addressX, lengthX);
            float[] yArr = NumpyToArray<float>(addressY, lengthY);

            Vector2[] vectors = new Vector2[xArr.Length];
            for (int i = 0; i < xArr.Length; i++)
            {
                vectors[i] = new Vector2(xArr[i], yArr[i]);
            }
            return vectors;
        }

        public static List<Coordinate[]> NumpyToCoordsList(
            long addressX, long lengthX,
            long addressY, long lengthY,
            long addressFirst, long lengthFirst,
            long addressNum, long lengthNum)
        {
            float[] xArr = NumpyToArray<float>(addressX, lengthX);
            float[] yArr = NumpyToArray<float>(addressY, lengthY);
            int[] firstArr = NumpyToArray<int>(addressFirst, lengthFirst);
            int[] numArr = NumpyToArray<int>(addressNum, lengthNum);
            List<Coordinate[]> output = new List<Coordinate[]>();
            for (int i = 0; i < firstArr.Length; i++)
            {
                int first = firstArr[i];
                int num = numArr[i];
                Coordinate[] coords = new Coordinate[num];
                for (int j = 0; j < num; j++)
                {
                    coords[j] = new Coordinate(xArr[first + j], yArr[first + j]);
                }
                output.Add(coords);
            }
            return output;
        }

        public static List<Vector2[]> NumpyToVector2List(
            long addressX, long lengthX,
            long addressY, long lengthY,
            long addressFirst, long lengthFirst,
            long addressNum, long lengthNum)
        {
            float[] xArr = NumpyToArray<float>(addressX, lengthX);
            float[] yArr = NumpyToArray<float>(addressY, lengthY);
            int[] firstArr = NumpyToArray<int>(addressFirst, lengthFirst);
            int[] numArr = NumpyToArray<int>(addressNum, lengthNum);
            List<Vector2[]> output = new List<Vector2[]>();
            for (int i = 0; i < firstArr.Length; i++)
            {
                int first = firstArr[i];
                int num = numArr[i];
                Vector2[] vectors = new Vector2[num];
                for (int j = 0; j < num; j++)
                {
                    vectors[j] = new Vector2(xArr[first + j], yArr[first + j]);
                }
                output.Add(vectors);
            }
            return output;
        }

        public static Color[] NumpyToColors(
            long addrR, long lenR, 
            long addrG, long lenG,
            long addrB, long lenB,
            long addrA, long lenA)
        {
            float[] arrR = NumpyToArray<float>(addrR, lenR);
            float[] arrG = NumpyToArray<float>(addrG, lenG);
            float[] arrB = NumpyToArray<float>(addrB, lenB);
            float[] arrA = NumpyToArray<float>(addrA, lenA);
            Color[] output = new Color[arrR.Length];
            for (int i = 0; i < output.Length; i++)
            {
                output[i] = new Color(arrR[i], arrG[i], arrB[i], arrA[i]);
            }
            return output;
        }


        public static List<T[]> SplitArray<T>(T[] polygonDatas, int maxChunks, int minItemPerChunk) where T : struct
        {
            int numChunks = maxChunks;
            numChunks = Math.Min(numChunks, polygonDatas.Length / minItemPerChunk);
            if (numChunks <= 1)
            {
                return new List<T[]> { polygonDatas };
            }
            int chunkSize = (int)Math.Ceiling((float)polygonDatas.Length / numChunks);
            List<T[]> chunks = new List<T[]>();

            int i = 0;
            while (true)
            {
                int offset = i * chunkSize;
                int remianSize = polygonDatas.Length - offset;
                int currentChunkSize = Math.Min(chunkSize, remianSize);
                T[] chunk = new T[currentChunkSize];

                Array.Copy(polygonDatas, offset, chunk, 0, currentChunkSize);
                chunks.Add(chunk);
                i++;
                if (remianSize <= chunkSize)
                    break;
            }
            return chunks;

        }

        public static Vector2[] CoordsToVector2(Coordinate[] coords)
        {
            Vector2[] o = new Vector2[coords.Length];
            for (int i = 0; i < coords.Length; i++)
            {
                Coordinate c = coords[i];
                o[i] = new Vector2((float)c.X, (float)c.Y);
            }
            return o;
        }

        public static Tuple<long, long> CoordToKey(Coordinate coord)
        {
            long x = Convert.ToInt64(coord.X * KEY_PRECISION);
            long y = Convert.ToInt64(coord.Y * KEY_PRECISION);

            Tuple<long, long> key = new Tuple<long, long>(x, y);
            return key;
        }

        public static Guid GenGuid()
        {
            return Guid.NewGuid();
        }

        public static Coordinate GenNull()
        {
            return null;
        }

        public static void Test(long addr1, long len1, long addr2, long len2, long addr3, long len3, long addr4, long len4)
        {
            float[] result1 = NumpyToArray<float>(addr1, len1);
            foreach (float i in result1) {Console.Write(i + "," ); }
            Console.WriteLine();
            float[] result2 = NumpyToArray<float>(addr2, len2);
            foreach (float i in result2) { Console.Write(i + ","); }
            Console.WriteLine();
            int[] result3 = NumpyToArray<int>(addr3, len3);
            foreach (int i in result3) { Console.Write(i + ","); }
            Console.WriteLine();
            int[] result4 = NumpyToArray<int>(addr4, len4);
            foreach (int i in result4) { Console.Write(i + ","); }
            Console.WriteLine();    
        }

    }

    public class Debug
    {
        public static void Log(string content)
        {
            Console.WriteLine(content);
        }
    }

    

}
