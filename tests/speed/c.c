extern int printf(char*, ...);
extern int rand();

int calculate(int a, int b, int c)
{
	return a+b*c-rand()+(a*b*c);
}

int main()
{
	printf("Calculation 1: %i", calculate(30, 40, 21));
	printf("Calculation 2: %i", calculate(49, 5, 70));

	const int res = calculate(30, 40, 50);

	return res-res;
}