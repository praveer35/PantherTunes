import java.util.Scanner;
import java.util.Arrays;

public class Solution {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int [] p = new int[n];
        for (int i = 0; i < n; i++) {
            p[i] = sc.nextInt();
        }
        Arrays.sort(p);
        long minUgly = 0;
        for (int i = 0; i < n - 1; i++) {
            minUgly += (long) ((p[i] - p[i + 1])) * (long) ((p[i] - p[i + 1]));
            //System.out.print(minUgly + ", ");
        }
        System.out.println(minUgly);
        for (int i = 0; i < n - 1; i++) {
            System.out.print(p[i] + " ");
        }
        if (n > 0) {
            System.out.println(p[n - 1]);
        }
    }
}

/*import java.util.Scanner;

public class Solution {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int [] s = new int[3];
        int [][] p = new int[n][2];
        //int [] conn = new int[n];
        int strength = 0;
        for (int i = 0; i < 3; i++) {
            s[i] = sc.nextInt();
        }
        for (int i = 0; i < n - 1; i++) {
            p[i][0] = sc.nextInt();
            p[i][1] = sc.nextInt();
        }
        if (s[0] >= s[1] && s[0] >= s[2]) {
            strength = (n - 1) * s[0];
        } else if (s[1] >= s[0] && s[1] >= s[2]) {
            //for (int i = 0; i < n; i++) {
            //    conn[p[i][0]]++;
            //    conn[p[i][1]]++;
            //}
            strength = (n - 1) * s[1];
            // holy drop on max
        } else {
            strength = (n - 1) * s[2];
        }
        System.out.println(strength);
    }
}*/

/*import java.util.Scanner;

public class Solution {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int m = sc.nextInt();
        int n = sc.nextInt();
        sc.nextLine();
        char [][] b = new char[m][n];
        int danger = 0;
        for (int i = 0; i < m; i++) {
            String row = sc.nextLine();
            for (int j = 0; j < n; j++) {
                b[i][j] = row.charAt(j);
            }
        }
        for (int i = 0; i < m; i++) {
            for (int j = 0; j < n; j++) {
                if (b[i][j] == '#')
                    continue;
                if (i != 0) {
                    if (b[i - 1][j] == '#')
                        danger++;
                    if (j != 0) {
                        if (b[i - 1][j - 1] == '#')
                            danger++;
                    }
                    if (j != n - 1) {
                        if (b[i - 1][j + 1] == '#')
                            danger++;
                    }
                }
                if (i != m - 1) {
                    if (b[i + 1][j] == '#')
                        danger++;
                    if (j != 0) {
                        if (b[i + 1][j - 1] == '#')
                            danger++;
                    }
                    if (j != n - 1) {
                        if (b[i + 1][j + 1] == '#')
                            danger++;
                    }
                }
                if (j != 0) {
                    if (b[i][j - 1] == '#')
                        danger++;
                }
                if (j != n - 1) {
                    if (b[i][j + 1] == '#')
                        danger++;
                }
            }
        }
        int maxDanger = 0;
        for (int i = 0; i < m; i++) {
            if (i == 0 || i == m - 1) {
                maxDanger += (n - 1) + (n/2);
            } else {
                maxDanger += 2 * (n/2) + (n - 1);
            }
        }
        if (danger < maxDanger) {
            System.out.println("YES");
        } else {
            System.out.println("NO");
        }
        int currDanger = 0;
        for (int i = 0; i < m; i++) {
            if (i == 0 || i == m - 1) {
                for (int j = 0; j < n; j++) {
                    currDanger += 
                }
            }
        }
    }
}*/