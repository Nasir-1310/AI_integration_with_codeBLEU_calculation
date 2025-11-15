#include <iostream>

int main() {
    int n;
    std::cout << "Enter the number of terms: ";
    std::cin >> n;

    int t1 = 0, t2 = 1;
    int nextTerm = 0;

    if (n <= 0) {
        std::cout << "Please enter a positive integer for the number of terms." << std::endl;
    } else if (n == 1) {
        std::cout << "Fibonacci Series: " << t1 << std::endl;
    } else {
        std::cout << "Fibonacci Series: " << t1 << ", " << t2;
        for (int i = 3; i <= n; ++i) {
            nextTerm = t1 + t2;
            std::cout << ", " << nextTerm;
            t1 = t2;
            t2 = nextTerm;
        }
        std::cout << std::endl;
    }

    return 0;
}