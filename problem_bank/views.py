from django.shortcuts import render


# Create your views here.
def mathematics_problem_view(request):
    return render(request, "templates/problems/multiple_choice/multiple_choice.html")
