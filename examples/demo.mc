// 答辩演示：读入 n，输出 1 到 n 的和、n 的阶乘，以及 n 的奇偶（偶数 0，奇数 1）
int n;
int i = 1;
int sum = 0;
int fact = 1;
read(n);
while (i <= n) {
    sum = sum + i;
    fact = fact * i;
    i = i + 1;
}
write(sum);
write(fact);
if (n - n / 2 * 2 == 0) {
    write(0);
} else {
    write(1);
}
