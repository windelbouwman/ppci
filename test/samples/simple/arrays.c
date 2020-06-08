// Demonstrates array handling

#include <stdio.h>

void print_board(register int (*board)[5])
{
    int i = 0;
    printf("=== BOARDS ===\n");
    for (i=0; board[i][0]; i++)
    {
        printf(
            "Board: %d, %d, %d, %d, %d\n",
            board[i][0],
            board[i][1],
            board[i][2],
            board[i][4],  // deliberately swap last two items here :)
            board[i][3]
            );
    }
    printf("===\n");
}

void print_board2(register int board[][5])
{
    int i = 0;
    printf("=== BOARDS2 ===\n");
    for (i=0; board[i][0]; i++)
    {
        printf(
            "Board: %d, %d, %d, %d, %d\n",
            board[i][0],
            board[i][1],
            board[i][3], // deliberately swap items here :)
            board[i][2],
            board[i][4]
            );
    }
    printf("===\n");
}

int g_boards[][5] = {
    {1337, 42, 0, 6, 99},
    {13, 37, -2, -1337, -880000},
    {1337, 42, 5000000, 6000000, 99},
    {0, 0, 0, 0, 0},
};

int main_main(void)
{
    print_board(g_boards);
    print_board2(g_boards);

    int l_boards[][5] = {
        {8722, 32700, -60000, 22, 0},
        {-600000, 800000, 1, 67, 101},
        {0, 0, 0, 0, 0},
    };

    print_board(l_boards);
}
